"""Tests for user.dat writer."""

from pathlib import Path

from lgus_dat.domain.employee import Employee
from lgus_dat.exporters.user_dat_writer import RECORD_SIZE, write_user_dat
from lgus_dat.importers.user_parser import parse_user_dat


def _build_user_record(user_id: int, name: str) -> bytes:
    record = bytearray(RECORD_SIZE)
    record[0] = user_id
    name_bytes = name.encode("utf-8")
    record[11 : 11 + len(name_bytes)] = name_bytes
    # Write string user ID at the device offset (byte 48, 24-byte field).
    string_id = str(user_id).encode("utf-8")
    record[48 : 48 + len(string_id)] = string_id
    # byte 39 is the constant 0x01 observed in device exports.
    record[39] = 0x01
    return bytes(record)


def test_write_user_dat_round_trip(tmp_path: Path) -> None:
    original = tmp_path / "user_original.dat"
    original.write_bytes(
        _build_user_record(1, "DELA CRUZ_C") + _build_user_record(2, "OMONGIA_J")
    )

    employees, _ = parse_user_dat(original)
    exported = tmp_path / "user_exported.dat"
    write_user_dat(employees, exported)

    reparsed, _ = parse_user_dat(exported)
    assert len(reparsed) == 2
    assert reparsed[0].device_user_id == "1"
    assert reparsed[0].name == "DELA CRUZ_C"
    assert reparsed[1].device_user_id == "2"
    assert reparsed[1].name == "OMONGIA_J"


def test_write_user_dat_edited_name(tmp_path: Path) -> None:
    original = tmp_path / "user_original.dat"
    original.write_bytes(_build_user_record(1, "DELA CRUZ_C"))

    employees, _ = parse_user_dat(original)
    edited = [Employee(device_user_id=emp.device_user_id, name="NEW NAME", raw_record=emp.raw_record) for emp in employees]

    exported = tmp_path / "user_exported.dat"
    write_user_dat(edited, exported)

    reparsed, _ = parse_user_dat(exported)
    assert reparsed[0].name == "NEW NAME"
    assert reparsed[0].device_user_id == "1"


def test_write_user_dat_new_employee(tmp_path: Path) -> None:
    employees = [Employee(device_user_id="5", name="GARCIA_J")]
    exported = tmp_path / "user_exported.dat"
    write_user_dat(employees, exported)

    reparsed, _ = parse_user_dat(exported)
    assert len(reparsed) == 1
    assert reparsed[0].device_user_id == "5"
    assert reparsed[0].name == "GARCIA_J"


def test_write_user_dat_preserves_string_user_id_offset(tmp_path: Path) -> None:
    """The exported user ID string must be at byte 48, not 50, for device compatibility."""
    original = tmp_path / "user_original.dat"
    original.write_bytes(_build_user_record(2, "OMONGIA_J"))

    employees, _ = parse_user_dat(original)
    exported = tmp_path / "user_exported.dat"
    write_user_dat(employees, exported)

    exported_bytes = exported.read_bytes()
    record = exported_bytes[:RECORD_SIZE]
    user_id_field = record[48:72].split(b"\x00")[0]
    assert user_id_field == b"2"
    assert record[39] == 0x01
