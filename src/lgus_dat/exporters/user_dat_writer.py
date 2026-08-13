"""Writer for ZKTeco/NGteco binary `user.dat` employee master files."""

from __future__ import annotations

from pathlib import Path

from lgus_dat.domain.employee import Employee

RECORD_SIZE = 72
NAME_OFFSET = 11
NAME_SIZE = 24
ENABLED_OFFSET = 40
USER_ID_STRING_OFFSET = 50
USER_ID_STRING_SIZE = 22


def _encode_name(name: str) -> bytes:
    return name.encode("latin-1", errors="replace")[:NAME_SIZE]


def _pack_string_id(user_id: str) -> bytes:
    return user_id.encode("latin-1", errors="replace")[:USER_ID_STRING_SIZE - 1]


def _default_record(user_id: str, name: str) -> bytes:
    record = bytearray(RECORD_SIZE)
    record[0] = int(user_id) if user_id.isdigit() else 0
    name_bytes = _encode_name(name)
    record[NAME_OFFSET : NAME_OFFSET + len(name_bytes)] = name_bytes
    record[ENABLED_OFFSET] = 1
    string_id = _pack_string_id(user_id)
    record[USER_ID_STRING_OFFSET : USER_ID_STRING_OFFSET + len(string_id)] = string_id
    return bytes(record)


def _update_record(record: bytes, user_id: str, name: str) -> bytes:
    updated = bytearray(record)
    updated[0] = int(user_id) if user_id.isdigit() else updated[0]

    # Clear and rewrite the name field.
    updated[NAME_OFFSET : NAME_OFFSET + NAME_SIZE] = b"\x00" * NAME_SIZE
    name_bytes = _encode_name(name)
    updated[NAME_OFFSET : NAME_OFFSET + len(name_bytes)] = name_bytes

    # Clear and rewrite the string user ID field.
    updated[USER_ID_STRING_OFFSET : USER_ID_STRING_OFFSET + USER_ID_STRING_SIZE] = (
        b"\x00" * USER_ID_STRING_SIZE
    )
    string_id = _pack_string_id(user_id)
    updated[USER_ID_STRING_OFFSET : USER_ID_STRING_OFFSET + len(string_id)] = string_id

    return bytes(updated)


def write_user_dat(employees: list[Employee], path: Path) -> None:
    """Write a list of Employee records to a binary `user.dat` file.

    If the employee was originally imported with a `raw_record`, the writer
    preserves the unknown header/tail bytes and updates only the fields it
    understands (numeric ID, name, and string ID). New employees are written
    using a default 72-byte record template.
    """
    with path.open("wb") as f:
        for employee in employees:
            if employee.raw_record:
                record = _update_record(employee.raw_record, employee.device_user_id, employee.name)
            else:
                record = _default_record(employee.device_user_id, employee.name)
            f.write(record)
