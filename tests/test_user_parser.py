"""Tests for user.dat parser."""

from pathlib import Path

from lgus_dat.importers.user_parser import parse_user_dat


def _build_user_record(user_id: int, name: str, record_size: int = 72) -> bytes:
    record = bytearray(record_size)
    record[0] = user_id
    name_bytes = name.encode("utf-8")
    record[11 : 11 + len(name_bytes)] = name_bytes
    return bytes(record)


def test_parse_user_dat(tmp_path: Path) -> None:
    dat_file = tmp_path / "user.dat"
    dat_file.write_bytes(
        _build_user_record(1, "DELA CRUZ_C") + _build_user_record(2, "OMONGIA_J")
    )

    employees, errors = parse_user_dat(dat_file)
    assert len(errors) == 0
    assert len(employees) == 2
    assert employees[0].device_user_id == "1"
    assert employees[0].name == "DELA CRUZ_C"
    assert employees[1].device_user_id == "2"
    assert employees[1].name == "OMONGIA_J"


def test_parse_user_dat_detects_short_file(tmp_path: Path) -> None:
    dat_file = tmp_path / "user.dat"
    dat_file.write_bytes(b"\x01short")

    employees, errors = parse_user_dat(dat_file)
    assert len(errors) == 2
    assert len(employees) == 0
