"""Tests for SQLite attendance registry."""

from pathlib import Path

from lgus_dat.domain.department import Department
from lgus_dat.domain.employee import Employee
from lgus_dat.persistence.registry import AttendanceRegistry


def test_registry_round_trip(tmp_path: Path) -> None:
    db = AttendanceRegistry(tmp_path / "test_registry.db")
    db.upsert_department(Department(department_id=1, name="Sales"))
    db.upsert_employee(Employee(device_user_id="1", name="DELA CRUZ_C", department_id=1))

    emp = db.get_employee("1")
    assert emp is not None
    assert emp.name == "DELA CRUZ_C"
    assert emp.department_id == 1
    assert db.employee_name("1") == "DELA CRUZ_C"

    dept = db.get_department(1)
    assert dept is not None
    assert dept.name == "Sales"


def test_registry_employee_without_department(tmp_path: Path) -> None:
    db = AttendanceRegistry(tmp_path / "test_registry.db")
    db.upsert_employee(Employee(device_user_id="42", name="UNKNOWN"))
    assert db.employee_name("42") == "UNKNOWN"
    assert db.employee_name("99") is None


def test_import_employees_preserves_local_edits(tmp_path: Path) -> None:
    db = AttendanceRegistry(tmp_path / "test_registry.db")
    db.upsert_department(Department(department_id=1, name="Sales"))
    db.upsert_employee(
        Employee(
            device_user_id="7",
            name="DELA CRUZ_C",
            full_name="Dela Cruz, Carlos",
            position="Clerk",
            department_id=1,
        )
    )

    # Simulate a user.dat re-import: device fields only, local fields unset.
    db.import_employees([Employee(device_user_id="7", name="DELA CRUZ_C.", raw_record=b"x")])

    emp = db.get_employee("7")
    assert emp is not None
    assert emp.name == "DELA CRUZ_C."
    assert emp.full_name == "Dela Cruz, Carlos"
    assert emp.position == "Clerk"
    assert emp.department_id == 1
    assert emp.raw_record == b"x"


def test_import_employees_does_not_blank_name(tmp_path: Path) -> None:
    db = AttendanceRegistry(tmp_path / "test_registry.db")
    db.upsert_employee(Employee(device_user_id="8", name="EXISTING"))

    db.import_employees([Employee(device_user_id="8", name="")])

    assert db.employee_name("8") == "EXISTING"
