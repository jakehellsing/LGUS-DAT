"""Tests for department.dat writer."""

from pathlib import Path

from lgus_dat.domain.department import Department
from lgus_dat.exporters.department_dat_writer import RECORD_SIZE, write_department_dat
from lgus_dat.importers.department_parser import parse_department_dat


def _build_department_record(dept_id: int, name: str) -> bytes:
    record = bytearray(RECORD_SIZE)
    record[0] = dept_id
    name_bytes = name.encode("utf-8")
    record[1 : 1 + len(name_bytes)] = name_bytes
    return bytes(record)


def test_write_department_dat_round_trip(tmp_path: Path) -> None:
    original = tmp_path / "department_original.dat"
    original.write_bytes(
        _build_department_record(1, "Sales") + _build_department_record(2, "Production")
    )

    departments, _ = parse_department_dat(original)
    exported = tmp_path / "department_exported.dat"
    write_department_dat(departments, exported)

    reparsed, _ = parse_department_dat(exported)
    assert len(reparsed) == 2
    assert reparsed[0].department_id == 1
    assert reparsed[0].name == "Sales"
    assert reparsed[1].department_id == 2
    assert reparsed[1].name == "Production"


def test_write_department_dat_edited_name(tmp_path: Path) -> None:
    original = tmp_path / "department_original.dat"
    original.write_bytes(_build_department_record(1, "Sales"))

    departments, _ = parse_department_dat(original)
    edited = [Department(department_id=dept.department_id, name="Marketing", raw_record=dept.raw_record) for dept in departments]

    exported = tmp_path / "department_exported.dat"
    write_department_dat(edited, exported)

    reparsed, _ = parse_department_dat(exported)
    assert reparsed[0].name == "Marketing"


def test_write_department_dat_new_department(tmp_path: Path) -> None:
    departments = [Department(department_id=5, name="R&D")]
    exported = tmp_path / "department_exported.dat"
    write_department_dat(departments, exported)

    reparsed, _ = parse_department_dat(exported)
    assert len(reparsed) == 1
    assert reparsed[0].department_id == 5
    assert reparsed[0].name == "R&D"
