"""SQLite-backed registry for employees and departments."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from lgus_dat.domain.department import Department
from lgus_dat.domain.employee import Employee


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
                    department_id INTEGER,
                    raw_record BLOB,
                    FOREIGN KEY (department_id) REFERENCES departments (department_id)
                );

                CREATE INDEX IF NOT EXISTS idx_employees_name ON employees (name);
                """
            )
            # Migrate older registries that may be missing the raw_record columns.
            if "raw_record" not in self._columns(conn, "departments"):
                conn.execute("ALTER TABLE departments ADD COLUMN raw_record BLOB")
            if "raw_record" not in self._columns(conn, "employees"):
                conn.execute("ALTER TABLE employees ADD COLUMN raw_record BLOB")
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
                INSERT INTO employees (device_user_id, name, department_id, raw_record)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(device_user_id) DO UPDATE SET
                    name = excluded.name,
                    department_id = excluded.department_id,
                    raw_record = excluded.raw_record
                """,
                (
                    employee.device_user_id,
                    employee.name,
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
                "SELECT device_user_id, name, department_id, raw_record FROM employees WHERE device_user_id = ?",
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
                "SELECT device_user_id, name, department_id, raw_record FROM employees ORDER BY device_user_id"
            ).fetchall()
        return [self._row_to_employee(row) for row in rows]

    def all_departments(self) -> list[Department]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT department_id, name, raw_record FROM departments ORDER BY department_id"
            ).fetchall()
        return [self._row_to_department(row) for row in rows]

    def employee_name(self, device_user_id: str) -> Optional[str]:
        emp = self.get_employee(device_user_id)
        return emp.name if emp else None

    def department_name(self, department_id: int) -> Optional[str]:
        dept = self.get_department(department_id)
        return dept.name if dept else None
