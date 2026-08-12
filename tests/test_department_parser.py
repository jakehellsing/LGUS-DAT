"""Tests for department.dat parser."""

from pathlib import Path

from lgus_dat.importers.department_parser import parse_department_dat


def _build_department_record(dept_id: int, name: str, record_size: int = 49) -> bytes:
    record = bytearray(record_size)
    record[0] = dept_id
    name_bytes = name.encode("utf-8")
    record[1 : 1 + len(name_bytes)] = name_bytes
    return bytes(record)


def test_parse_department_dat(tmp_path: Path) -> None:
    dat_file = tmp_path / "department.dat"
    dat_file.write_bytes(
        _build_department_record(1, "Sales")
        + _build_department_record(2, "Production")
    )

    departments, errors = parse_department_dat(dat_file)
    assert len(errors) == 0
    assert len(departments) == 2
    assert departments[0].department_id == 1
    assert departments[0].name == "Sales"
    assert departments[1].department_id == 2
    assert departments[1].name == "Production"
