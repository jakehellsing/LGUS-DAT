"""SQLite-backed registry for employees, departments, and attendance logs."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from lgus_dat.domain.biometric_template import BiometricTemplate
from lgus_dat.domain.department import Department
from lgus_dat.domain.employee import Employee
from lgus_dat.parser.dat_parser import ParsedRecord


class AttendanceRegistry:
    """Local registry that maps device user/department IDs to human-readable data."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or Path("lgus_registry.db")
        self._init_db()

    def _connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _columns(self, conn: sqlite3.Connection, table: str) -> set[str]:
        cursor = conn.execute(f"PRAGMA table_info({table})")
        return {row["name"] for row in cursor.fetchall()}

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS departments (
                    department_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    raw_record BLOB
                );

                CREATE TABLE IF NOT EXISTS employees (
                    device_user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    full_name TEXT,
                    position TEXT,
                    department_id INTEGER,
                    raw_record BLOB,
                    FOREIGN KEY (department_id) REFERENCES departments (department_id)
                );

                CREATE INDEX IF NOT EXISTS idx_employees_name ON employees (name);

                CREATE TABLE IF NOT EXISTS attendance_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    log_date TEXT NOT NULL,
                    log_time TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    original_line TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    imported_at TEXT NOT NULL,
                    UNIQUE(employee_id, timestamp, original_line, source_file)
                );

                CREATE INDEX IF NOT EXISTS idx_attendance_logs_employee ON attendance_logs (employee_id);
                CREATE INDEX IF NOT EXISTS idx_attendance_logs_date ON attendance_logs (log_date);
                CREATE INDEX IF NOT EXISTS idx_attendance_logs_source ON attendance_logs (source_file);

                CREATE TABLE IF NOT EXISTS biotemplates (
                    pin TEXT NOT NULL,
                    no INTEGER NOT NULL,
                    index_no INTEGER NOT NULL,
                    valid INTEGER NOT NULL DEFAULT 1,
                    duress INTEGER NOT NULL DEFAULT 0,
                    type INTEGER NOT NULL DEFAULT 0,
                    major_ver INTEGER NOT NULL DEFAULT 0,
                    minor_ver INTEGER NOT NULL DEFAULT 0,
                    format INTEGER NOT NULL DEFAULT 0,
                    tmp TEXT NOT NULL,
                    PRIMARY KEY (pin, no, index_no)
                );

                CREATE TABLE IF NOT EXISTS template_files (
                    filename TEXT PRIMARY KEY,
                    content BLOB NOT NULL
                );
                """
            )
            # Migrate older registries that may be missing the raw_record columns.
            if "raw_record" not in self._columns(conn, "departments"):
                conn.execute("ALTER TABLE departments ADD COLUMN raw_record BLOB")
            if "raw_record" not in self._columns(conn, "employees"):
                conn.execute("ALTER TABLE employees ADD COLUMN raw_record BLOB")
            if "full_name" not in self._columns(conn, "employees"):
                conn.execute("ALTER TABLE employees ADD COLUMN full_name TEXT")
            if "position" not in self._columns(conn, "employees"):
                conn.execute("ALTER TABLE employees ADD COLUMN position TEXT")
            conn.commit()

    def upsert_department(self, department: Department) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO departments (department_id, name, raw_record)
                VALUES (?, ?, ?)
                ON CONFLICT(department_id) DO UPDATE SET
                    name = excluded.name,
                    raw_record = excluded.raw_record
                """,
                (
                    department.department_id,
                    department.name,
                    department.raw_record,
                ),
            )
            conn.commit()

    def upsert_employee(self, employee: Employee) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO employees (device_user_id, name, full_name, position, department_id, raw_record)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(device_user_id) DO UPDATE SET
                    name = excluded.name,
                    full_name = excluded.full_name,
                    position = excluded.position,
                    department_id = excluded.department_id,
                    raw_record = excluded.raw_record
                """,
                (
                    employee.device_user_id,
                    employee.name,
                    employee.full_name,
                    employee.position,
                    employee.department_id,
                    employee.raw_record,
                ),
            )
            conn.commit()

    def delete_employee(self, device_user_id: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "DELETE FROM employees WHERE device_user_id = ?",
                (device_user_id,),
            )
            conn.commit()

    def delete_department(self, department_id: int) -> None:
        with self._connection() as conn:
            conn.execute(
                "DELETE FROM departments WHERE department_id = ?",
                (department_id,),
            )
            conn.commit()

    def import_departments(self, departments: list[Department]) -> int:
        count = 0
        for dept in departments:
            self.upsert_department(dept)
            count += 1
        return count

    def import_employees(self, employees: list[Employee]) -> int:
        count = 0
        for emp in employees:
            self.upsert_employee(emp)
            count += 1
        return count

    def _row_to_employee(self, row: sqlite3.Row) -> Employee:
        return Employee(
            device_user_id=row["device_user_id"],
            name=row["name"],
            full_name=row["full_name"],
            position=row["position"],
            department_id=row["department_id"],
            raw_record=row["raw_record"],
        )

    def _row_to_department(self, row: sqlite3.Row) -> Department:
        return Department(
            department_id=row["department_id"],
            name=row["name"],
            raw_record=row["raw_record"],
        )

    def get_employee(self, device_user_id: str) -> Optional[Employee]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT device_user_id, name, full_name, position, department_id, raw_record FROM employees WHERE device_user_id = ?",
                (device_user_id,),
            ).fetchone()
        if row:
            return self._row_to_employee(row)
        return None

    def get_department(self, department_id: int) -> Optional[Department]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT department_id, name, raw_record FROM departments WHERE department_id = ?",
                (department_id,),
            ).fetchone()
        if row:
            return self._row_to_department(row)
        return None

    def all_employees(self) -> list[Employee]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT device_user_id, name, full_name, position, department_id, raw_record FROM employees"
            ).fetchall()
        employees = [self._row_to_employee(row) for row in rows]
        employees.sort(key=lambda e: (int(e.device_user_id) if e.device_user_id.isdigit() else float("inf"), e.device_user_id.lower()))
        return employees

    def all_departments(self) -> list[Department]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT department_id, name, raw_record FROM departments ORDER BY department_id"
            ).fetchall()
        return [self._row_to_department(row) for row in rows]

    def _row_to_biotemplate(self, row: sqlite3.Row) -> BiometricTemplate:
        return BiometricTemplate(
            pin=row["pin"],
            no=row["no"],
            index=row["index_no"],
            valid=row["valid"],
            duress=row["duress"],
            type=row["type"],
            major_ver=row["major_ver"],
            minor_ver=row["minor_ver"],
            format=row["format"],
            tmp=row["tmp"],
        )

    def upsert_biotemplate(self, template: BiometricTemplate) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO biotemplates (pin, no, index_no, valid, duress, type, major_ver, minor_ver, format, tmp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(pin, no, index_no) DO UPDATE SET
                    valid = excluded.valid,
                    duress = excluded.duress,
                    type = excluded.type,
                    major_ver = excluded.major_ver,
                    minor_ver = excluded.minor_ver,
                    format = excluded.format,
                    tmp = excluded.tmp
                """,
                (
                    template.pin,
                    template.no,
                    template.index,
                    template.valid,
                    template.duress,
                    template.type,
                    template.major_ver,
                    template.minor_ver,
                    template.format,
                    template.tmp,
                ),
            )
            conn.commit()

    def import_biotemplates(self, templates: list[BiometricTemplate]) -> int:
        count = 0
        for template in templates:
            self.upsert_biotemplate(template)
            count += 1
        return count

    def all_biotemplates(self) -> list[BiometricTemplate]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT pin, no, index_no, valid, duress, type, major_ver, minor_ver, format, tmp FROM biotemplates ORDER BY pin"
            ).fetchall()
        templates = [self._row_to_biotemplate(row) for row in rows]
        templates.sort(key=lambda t: (int(t.pin) if t.pin.isdigit() else float("inf"), t.no, t.index))
        return templates

    def biotemplates_for_pin(self, pin: str) -> list[BiometricTemplate]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT pin, no, index_no, valid, duress, type, major_ver, minor_ver, format, tmp FROM biotemplates WHERE pin = ? ORDER BY no, index_no",
                (pin,),
            ).fetchall()
        return [self._row_to_biotemplate(row) for row in rows]

    def update_biotemplate_pin(self, old_pin: str, new_pin: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE biotemplates SET pin = ? WHERE pin = ?",
                (new_pin, old_pin),
            )
            conn.commit()

    def delete_biotemplates_for_pin(self, pin: str) -> None:
        with self._connection() as conn:
            conn.execute("DELETE FROM biotemplates WHERE pin = ?", (pin,))
            conn.commit()

    def import_template_files(self, files: dict[str, bytes]) -> int:
        with self._connection() as conn:
            count = 0
            for filename, content in files.items():
                conn.execute(
                    "INSERT INTO template_files (filename, content) VALUES (?, ?) ON CONFLICT(filename) DO UPDATE SET content = excluded.content",
                    (filename, content),
                )
                count += 1
            conn.commit()
        return count

    def all_template_files(self) -> dict[str, bytes]:
        with self._connection() as conn:
            rows = conn.execute("SELECT filename, content FROM template_files ORDER BY filename").fetchall()
        return {row["filename"]: row["content"] for row in rows}

    def employee_name(self, device_user_id: str) -> Optional[str]:
        emp = self.get_employee(device_user_id)
        return emp.name if emp else None

    def department_name(self, department_id: int) -> Optional[str]:
        dept = self.get_department(department_id)
        return dept.name if dept else None

    def import_attendance_logs(
        self,
        records: list[ParsedRecord],
        source_file: Path,
    ) -> int:
        """Store raw attendance records, skipping exact duplicates for this source."""
        imported_at = datetime.now().isoformat()
        source = str(source_file)
        with self._connection() as conn:
            changes_before = conn.total_changes
            for record in records:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO attendance_logs
                    (employee_id, log_date, log_time, timestamp, original_line, source_file, imported_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.employee_id,
                        record.timestamp.date().isoformat(),
                        record.timestamp.strftime("%H:%M:%S"),
                        record.timestamp.isoformat(),
                        record.original_line,
                        source,
                        imported_at,
                    ),
                )
            conn.commit()
            return conn.total_changes - changes_before

    def get_attendance_logs(self) -> list[ParsedRecord]:
        """Return all stored attendance logs, ordered by timestamp then original line."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT employee_id, timestamp, original_line
                FROM attendance_logs
                ORDER BY timestamp, original_line
                """
            ).fetchall()

        records: list[ParsedRecord] = []
        for row in rows:
            timestamp = datetime.fromisoformat(row["timestamp"])
            original_line = row["original_line"]
            fields = tuple(original_line.split())
            records.append(
                ParsedRecord(
                    employee_id=row["employee_id"],
                    timestamp=timestamp,
                    original_line=original_line,
                    fields=fields,
                )
            )
        return records

    def count_attendance_logs(self) -> int:
        with self._connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM attendance_logs").fetchone()
        return row[0] if row else 0

    def get_attendance_log_sources(self) -> list[str]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT source_file FROM attendance_logs ORDER BY source_file"
            ).fetchall()
        return [row["source_file"] for row in rows]
