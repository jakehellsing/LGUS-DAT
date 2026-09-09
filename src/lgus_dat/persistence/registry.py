"""SQLite-backed registry for employees, departments, and attendance logs."""

from __future__ import annotations

import sqlite3
import sys
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from lgus_dat.domain.attendance_filing import AttendanceFiling
from lgus_dat.domain.biometric_template import BiometricTemplate
from lgus_dat.domain.department import Department
from lgus_dat.domain.employee import Employee
from lgus_dat.domain.holiday import Holiday
from lgus_dat.parser.dat_parser import ParsedRecord


DEFAULT_DEPARTMENTS: list[Department] = [
    Department(department_id=1, name="OFFICE OF THE MUNICIPAL MAYOR", head_name="Hon. Joel Molina Ventura", head_position="Municipal Mayor"),
    Department(department_id=2, name="OFFICE OF THE MUNICIPAL ACCOUNTANT", head_name="Johnmar A. Jaipuddin", head_position="MGDH - I Mun. Accountant"),
    Department(department_id=3, name="OFFICE OF THE MUNICIPAL ADMINISTRATOR", head_name="Ruth Molina Ventura", head_position="Municipal Administrator"),
    Department(department_id=4, name="OFFICE OF THE MUNICIPAL HUMAN RESOURCE MANAGEMENT OFFICER", head_name="Lilamay Unadi Surbito", head_position="MHRMO"),
    Department(department_id=5, name="OFFICE OF THE MUNICIPAL AGRICULTURIST", head_name="Adelyn D. Rivera", head_position="Municipal Agriculturist"),
    Department(department_id=6, name="OFFICE OF THE MUNICIPAL TREASURER", head_name="Mely Rose Daguno Manuel", head_position="Municipal Treasurer"),
    Department(department_id=7, name="OFFICE OF THE MUNICIPAL ASSESSOR", head_name="Alhan Mamang Naing", head_position="Municipal Assessor"),
    Department(department_id=8, name="OFFICE OF THE MUNICIPAL BUDGET OFFICER", head_name="Richelle Joanne T. Duhig", head_position="Municipal Budget Officer"),
    Department(department_id=9, name="OFFICE OF THE MUNICIPAL COOPERATIVE OFFICER", head_name="Beverly Sunshine P. Maninang", head_position="Municipal Cooperative Officer"),
    Department(department_id=10, name="OFFICE OF THE MUNICIPAL ENGINEER", head_name="Anwar Kenny Andrew F. Amilasan", head_position="Municipal Engineer"),
    Department(department_id=11, name="OFFICE OF THE MUNICIPAL CIVIL REGISTRAR", head_name="Hadjinil Naing Pingli", head_position="Municipal Civil Registrar"),
    Department(department_id=12, name="OFFICE OF THE MUNICIPAL LEGAL OFFICER", head_name="", head_position="MGDH - I Mun. Legal Officer"),
    Department(department_id=13, name="OFFICE OF THE MUNICIPAL DISASTER RISK REDUCTION MANAGEMENT OFFICER", head_name="Majid J. Arasad", head_position="MDRRMO Officer"),
    Department(department_id=14, name="OFFICE OF THE MUNICIPAL ENVIRONMENT AND NATURAL RESOURCES OFFICER", head_name="", head_position="MENRO"),
    Department(department_id=15, name="OFFICE OF THE MUNICIPAL GENERAL SERVICE OFFICER", head_name="Janice L. Vitug", head_position="MGDH - I Mun. General Services Officer"),
    Department(department_id=16, name="OFFICE OF THE MUNICIPAL PLANNING AND DEVELOPMENT CENTER", head_name="Engr. Ricardo L. Genturalez", head_position="MPDO"),
    Department(department_id=17, name="OFFICE OF THE MSWDO", head_name="Suralda Asid Mandi", head_position="MSWDO"),
    Department(department_id=18, name="PESO", head_name="Daud Bakil", head_position="Peso Manager"),
    Department(department_id=19, name="RHU", head_name="Dra. Derileen D. Edding", head_position="Municipal Health Officer"),
]

# Bumping this value will re-seed DEFAULT_DEPARTMENTS and overwrite department rows.
DEPARTMENT_SEED_VERSION = "1"

DEFAULT_LEAVE_TYPES: list[str] = [
    "Vacation Leave",
    "Mandatory/Forced Leave",
    "Sick Leave",
    "Maternity Leave",
    "Paternity Leave",
    "Special Privilege Leave",
    "Solo Parent Leave",
    "Study Leave",
    "10-Day VAWC Leave",
    "Rehabilitation Privilege",
    "Special Leave Benefits for Women",
    "Special Emergency (Calamity) Leave",
    "Adoption Leave",
    "Fieldwork",
]

# Bumping this value will re-seed DEFAULT_LEAVE_TYPES and overwrite leave_type rows.
LEAVE_TYPE_SEED_VERSION = "1"


def _default_db_path() -> Path:
    """Return the default database path next to the executable when bundled."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path.cwd()
    return base / "lgus_registry.db"


class AttendanceRegistry:
    """Local registry that maps device user/department IDs to human-readable data."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or _default_db_path()
        self._init_db()

    def _connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _columns(self, conn: sqlite3.Connection, table: str) -> set[str]:
        cursor = conn.execute(f"PRAGMA table_info({table})")
        return {row["name"] for row in cursor.fetchall()}

    def _tables(self, conn: sqlite3.Connection) -> set[str]:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return {row["name"] for row in cursor.fetchall()}

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS departments (
                    department_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    raw_record BLOB,
                    head_name TEXT,
                    head_position TEXT
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

                CREATE TABLE IF NOT EXISTS positions (
                    name TEXT PRIMARY KEY
                );

                CREATE TABLE IF NOT EXISTS leave_types (
                    name TEXT PRIMARY KEY
                );

                CREATE TABLE IF NOT EXISTS holidays (
                    holiday_date TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS employee_status_filings (
                    filing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (employee_id) REFERENCES employees (device_user_id)
                );

                CREATE INDEX IF NOT EXISTS idx_status_filings_employee ON employee_status_filings (employee_id);
                CREATE INDEX IF NOT EXISTS idx_status_filings_dates ON employee_status_filings (start_date, end_date);

                CREATE TABLE IF NOT EXISTS seed_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS dtr_slot_overrides (
                    employee_id TEXT NOT NULL,
                    override_date TEXT NOT NULL,
                    slot TEXT NOT NULL,
                    punch_time TEXT NOT NULL,
                    PRIMARY KEY (employee_id, override_date, slot),
                    FOREIGN KEY (employee_id) REFERENCES employees (device_user_id)
                );

                CREATE INDEX IF NOT EXISTS idx_dtr_overrides_employee ON dtr_slot_overrides (employee_id);
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
            if "head_name" not in self._columns(conn, "departments"):
                conn.execute("ALTER TABLE departments ADD COLUMN head_name TEXT")
            if "head_position" not in self._columns(conn, "departments"):
                conn.execute("ALTER TABLE departments ADD COLUMN head_position TEXT")
            if "positions" not in self._tables(conn):
                conn.execute(
                    """
                    CREATE TABLE positions (
                        name TEXT PRIMARY KEY
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT OR IGNORE INTO positions (name)
                    SELECT DISTINCT position FROM employees WHERE position IS NOT NULL
                    """
                )

            stored_version = conn.execute(
                "SELECT value FROM seed_metadata WHERE key = 'department_seed_version'"
            ).fetchone()
            if stored_version is None or stored_version["value"] != DEPARTMENT_SEED_VERSION:
                self._seed_departments(conn)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO seed_metadata (key, value)
                    VALUES ('department_seed_version', ?)
                    """,
                    (DEPARTMENT_SEED_VERSION,),
                )

            stored_leave_version = conn.execute(
                "SELECT value FROM seed_metadata WHERE key = 'leave_type_seed_version'"
            ).fetchone()
            if stored_leave_version is None or stored_leave_version["value"] != LEAVE_TYPE_SEED_VERSION:
                self._seed_leave_types(conn)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO seed_metadata (key, value)
                    VALUES ('leave_type_seed_version', ?)
                    """,
                    (LEAVE_TYPE_SEED_VERSION,),
                )

            conn.commit()

    def _seed_departments(self, conn: sqlite3.Connection) -> None:
        """Reset departments to the canonical default list."""
        conn.execute("DELETE FROM departments")
        conn.executemany(
            """
            INSERT INTO departments (department_id, name, raw_record, head_name, head_position)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    dept.department_id,
                    dept.name,
                    dept.raw_record,
                    dept.head_name,
                    dept.head_position,
                )
                for dept in DEFAULT_DEPARTMENTS
            ],
        )

    def _seed_leave_types(self, conn: sqlite3.Connection) -> None:
        """Reset leave types to the canonical default list."""
        conn.execute("DELETE FROM leave_types")
        conn.executemany(
            "INSERT INTO leave_types (name) VALUES (?)",
            [(name,) for name in DEFAULT_LEAVE_TYPES],
        )

    def upsert_department(self, department: Department) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO departments (department_id, name, raw_record, head_name, head_position)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(department_id) DO UPDATE SET
                    name = excluded.name,
                    raw_record = excluded.raw_record,
                    head_name = excluded.head_name,
                    head_position = excluded.head_position
                """,
                (
                    department.department_id,
                    department.name,
                    department.raw_record,
                    department.head_name,
                    department.head_position,
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

    def bulk_update_department(
        self,
        employee_ids: list[str],
        department_id: int | None,
    ) -> int:
        """Update the department assignment for many employees at once."""
        if not employee_ids:
            return 0
        with self._connection() as conn:
            placeholders = ",".join("?" for _ in employee_ids)
            result = conn.execute(
                f"UPDATE employees SET department_id = ? WHERE device_user_id IN ({placeholders})",
                (department_id, *employee_ids),
            )
            conn.commit()
            return result.rowcount

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
            head_name=row["head_name"],
            head_position=row["head_position"],
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
                "SELECT department_id, name, raw_record, head_name, head_position FROM departments WHERE department_id = ?",
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
                "SELECT department_id, name, raw_record, head_name, head_position FROM departments ORDER BY department_id"
            ).fetchall()
        return [self._row_to_department(row) for row in rows]

    def department_head_name(self, department_id: int) -> Optional[str]:
        dept = self.get_department(department_id)
        return dept.head_name if dept else None

    def department_head_position(self, department_id: int) -> Optional[str]:
        dept = self.get_department(department_id)
        return dept.head_position if dept else None

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

    def all_positions(self) -> list[str]:
        """Return all position names in alphabetical order."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT name FROM positions ORDER BY name"
            ).fetchall()
        return [row["name"] for row in rows]

    def add_position(self, name: str) -> None:
        """Insert a new position name."""
        with self._connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO positions (name) VALUES (?)",
                (name,),
            )
            conn.commit()

    def rename_position(self, old_name: str, new_name: str) -> None:
        """Rename a position and update all employees using it."""
        with self._connection() as conn:
            conn.execute(
                "UPDATE OR IGNORE positions SET name = ? WHERE name = ?",
                (new_name, old_name),
            )
            conn.execute(
                "UPDATE employees SET position = ? WHERE position = ?",
                (new_name, old_name),
            )
            conn.commit()

    def delete_position(self, name: str) -> None:
        """Delete a position and clear it from employees."""
        with self._connection() as conn:
            conn.execute("DELETE FROM positions WHERE name = ?", (name,))
            conn.execute(
                "UPDATE employees SET position = NULL WHERE position = ?",
                (name,),
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Leave / attendance status types
    # ------------------------------------------------------------------

    def all_leave_types(self) -> list[str]:
        """Return all leave/attendance status types in alphabetical order."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT name FROM leave_types ORDER BY name"
            ).fetchall()
        return [row["name"] for row in rows]

    def add_leave_type(self, name: str) -> None:
        """Insert a new leave/attendance status type."""
        with self._connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO leave_types (name) VALUES (?)",
                (name,),
            )
            conn.commit()

    def rename_leave_type(self, old_name: str, new_name: str) -> None:
        """Rename a status type and update all filings using it."""
        with self._connection() as conn:
            conn.execute(
                "UPDATE OR IGNORE leave_types SET name = ? WHERE name = ?",
                (new_name, old_name),
            )
            conn.execute(
                "UPDATE employee_status_filings SET status = ? WHERE status = ?",
                (new_name, old_name),
            )
            conn.commit()

    def delete_leave_type(self, name: str) -> None:
        """Delete a status type and remove filings that use it."""
        with self._connection() as conn:
            conn.execute("DELETE FROM leave_types WHERE name = ?", (name,))
            conn.execute(
                "DELETE FROM employee_status_filings WHERE status = ?",
                (name,),
            )
            conn.commit()

    # ------------------------------------------------------------------
    # System-wide holidays
    # ------------------------------------------------------------------

    def upsert_holiday(self, holiday: Holiday) -> None:
        """Insert or replace a system-wide holiday."""
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO holidays (holiday_date, name)
                VALUES (?, ?)
                ON CONFLICT(holiday_date) DO UPDATE SET
                    name = excluded.name
                """,
                (holiday.holiday_date.isoformat(), holiday.name),
            )
            conn.commit()

    def delete_holiday(self, holiday_date: date) -> None:
        """Delete a system-wide holiday by date."""
        with self._connection() as conn:
            conn.execute(
                "DELETE FROM holidays WHERE holiday_date = ?",
                (holiday_date.isoformat(),),
            )
            conn.commit()

    def all_holidays(self) -> list[Holiday]:
        """Return all holidays in date order."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT holiday_date, name FROM holidays ORDER BY holiday_date"
            ).fetchall()
        return [Holiday(holiday_date=date.fromisoformat(row["holiday_date"]), name=row["name"]) for row in rows]

    def get_holidays_for_month(self, year: int, month: int) -> dict[int, str]:
        """Return a mapping of day-of-month to holiday name for a given month."""
        first = date(year, month, 1).isoformat()
        last = date(year, month, monthrange(year, month)[1]).isoformat()
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT holiday_date, name FROM holidays WHERE holiday_date BETWEEN ? AND ? ORDER BY holiday_date",
                (first, last),
            ).fetchall()
        return {date.fromisoformat(row["holiday_date"]).day: row["name"] for row in rows}

    # ------------------------------------------------------------------
    # Employee attendance status filings
    # ------------------------------------------------------------------

    def file_employee_status(self, filing: AttendanceFiling) -> None:
        """Store an employee attendance status filing over a date range."""
        created_at = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO employee_status_filings
                (employee_id, start_date, end_date, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    filing.employee_id,
                    filing.start_date.isoformat(),
                    filing.end_date.isoformat(),
                    filing.status,
                    created_at,
                ),
            )
            conn.commit()

    def delete_employee_status_filing(self, filing_id: int) -> None:
        """Delete an employee attendance status filing."""
        with self._connection() as conn:
            conn.execute(
                "DELETE FROM employee_status_filings WHERE filing_id = ?",
                (filing_id,),
            )
            conn.commit()

    def all_employee_status_filings(self) -> list[AttendanceFiling]:
        """Return all employee status filings, most recent first."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT filing_id, employee_id, start_date, end_date, status
                FROM employee_status_filings
                ORDER BY start_date DESC, filing_id DESC
                """
            ).fetchall()
        return [
            AttendanceFiling(
                filing_id=row["filing_id"],
                employee_id=row["employee_id"],
                start_date=date.fromisoformat(row["start_date"]),
                end_date=date.fromisoformat(row["end_date"]),
                status=row["status"],
            )
            for row in rows
        ]

    def get_employee_status_for_month(
        self,
        employee_id: str,
        year: int,
        month: int,
    ) -> dict[int, list[str]]:
        """Return a mapping of day-of-month to status labels for an employee."""
        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT start_date, end_date, status
                FROM employee_status_filings
                WHERE employee_id = ?
                  AND start_date <= ?
                  AND end_date >= ?
                ORDER BY created_at
                """,
                (employee_id, last_day.isoformat(), first_day.isoformat()),
            ).fetchall()

        result: dict[int, list[str]] = {}
        for row in rows:
            start = date.fromisoformat(row["start_date"])
            end = date.fromisoformat(row["end_date"])
            status = row["status"]
            range_start = max(start, first_day)
            range_end = min(end, last_day)
            current = range_start
            while current <= range_end:
                result.setdefault(current.day, []).append(status)
                current += timedelta(days=1)
        return result

    def save_dtr_overrides_for_employee(
        self,
        employee_id: str,
        overrides: dict[date, dict[str, str]],
    ) -> None:
        """Persist DTR slot overrides for a given employee."""
        with self._connection() as conn:
            conn.execute(
                "DELETE FROM dtr_slot_overrides WHERE employee_id = ?",
                (employee_id,),
            )
            for override_date, slots in overrides.items():
                for slot, punch_time in slots.items():
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO dtr_slot_overrides
                        (employee_id, override_date, slot, punch_time)
                        VALUES (?, ?, ?, ?)
                        """,
                        (employee_id, override_date.isoformat(), slot, punch_time),
                    )
            conn.commit()

    def get_dtr_overrides(self) -> dict[str, dict[date, dict[str, str]]]:
        """Return all stored DTR slot overrides keyed by employee and date."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT employee_id, override_date, slot, punch_time
                FROM dtr_slot_overrides
                ORDER BY employee_id, override_date, slot
                """
            ).fetchall()

        overrides: dict[str, dict[date, dict[str, str]]] = {}
        for row in rows:
            emp_id = row["employee_id"]
            override_date = date.fromisoformat(row["override_date"])
            slot = row["slot"]
            punch_time = row["punch_time"]
            employee_overrides = overrides.setdefault(emp_id, {})
            day_overrides = employee_overrides.setdefault(override_date, {})
            day_overrides[slot] = punch_time
        return overrides
