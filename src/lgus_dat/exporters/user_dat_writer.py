"""Writer for ZKTeco/NGteco binary `user.dat` employee master files."""

from __future__ import annotations

import struct
from pathlib import Path

from lgus_dat.domain.employee import Employee

RECORD_SIZE = 72
NAME_OFFSET = 11
NAME_SIZE = 24
PASSWORD_SIZE = 8
GROUP_ID_SIZE = 7
USER_ID_SIZE = 24


def _encode_name(name: str) -> bytes:
    return name.encode("latin-1", errors="replace")[:NAME_SIZE]


def _encode_password(password: str) -> bytes:
    return password.encode("latin-1", errors="replace")[:PASSWORD_SIZE]


def _encode_group_id(group_id: str) -> bytes:
    return group_id.encode("latin-1", errors="replace")[:GROUP_ID_SIZE]


def _encode_user_id(user_id: str) -> bytes:
    return user_id.encode("latin-1", errors="replace")[:USER_ID_SIZE]


def _read_field_from_raw(raw_record: bytes, offset: int, size: int) -> str:
    """Read a null-terminated string from the raw record at a known offset."""
    return raw_record[offset : offset + size].split(b"\x00")[0].decode("latin-1", errors="replace")


def _uid_from_employee(employee: Employee) -> int:
    if employee.uid is not None:
        return employee.uid
    if employee.raw_record and len(employee.raw_record) == RECORD_SIZE:
        return struct.unpack("<H", employee.raw_record[0:2])[0]
    if employee.device_user_id.isdigit():
        return int(employee.device_user_id)
    return 0


def _write_field(record: bytearray, offset: int, data: bytes, size: int) -> None:
    record[offset : offset + size] = b"\x00" * size
    record[offset : offset + len(data)] = data


def _pack_record(employee: Employee) -> bytes:
    """Pack an Employee into the ZK8 72-byte `user.dat` record layout."""
    record = bytearray(RECORD_SIZE)

    # Start from the original raw record when available so unknown/proprietary
    # bytes (e.g. byte 39 constant, padding) survive a round trip.
    if employee.raw_record and len(employee.raw_record) == RECORD_SIZE:
        record[:] = employee.raw_record
    else:
        # New employee default: constant at byte 39, enabled, empty fields.
        record[39] = 0x01

    uid = _uid_from_employee(employee)
    record[0:2] = struct.pack("<H", uid)

    privilege = employee.privilege
    if privilege is None and employee.raw_record and len(employee.raw_record) == RECORD_SIZE:
        privilege = employee.raw_record[2]
    record[2] = privilege if privilege is not None else 0

    password = employee.password
    if password is None and employee.raw_record and len(employee.raw_record) == RECORD_SIZE:
        password = _read_field_from_raw(employee.raw_record, 3, PASSWORD_SIZE)
    _write_field(record, 3, _encode_password(password or ""), PASSWORD_SIZE)

    _write_field(record, NAME_OFFSET, _encode_name(employee.name), NAME_SIZE)

    card = employee.card
    if card is None and employee.raw_record and len(employee.raw_record) == RECORD_SIZE:
        card = struct.unpack("<I", employee.raw_record[35:39])[0]
    record[35:39] = struct.pack("<I", card if card is not None else 0)

    # byte 39 is the constant 0x01 observed in device exports; preserve if raw
    # exists, otherwise already set above.
    if not (employee.raw_record and len(employee.raw_record) == RECORD_SIZE):
        record[39] = 0x01

    group_id = employee.group_id
    if group_id is None and employee.raw_record and len(employee.raw_record) == RECORD_SIZE:
        group_id = _read_field_from_raw(employee.raw_record, 40, GROUP_ID_SIZE)
    _write_field(record, 40, _encode_group_id(group_id or ""), GROUP_ID_SIZE)
    record[47] = 0x00  # padding byte

    user_id = employee.device_user_id
    _write_field(record, 48, _encode_user_id(user_id), USER_ID_SIZE)

    return bytes(record)


def write_user_dat(employees: list[Employee], path: Path) -> None:
    """Write a list of Employee records to a binary `user.dat` file.

    The output follows the ZKTeco/NGteco ZK8 72-byte record layout so it can be
    imported back into the device without shifting IDs or names.
    """
    with path.open("wb") as f:
        for employee in employees:
            f.write(_pack_record(employee))
