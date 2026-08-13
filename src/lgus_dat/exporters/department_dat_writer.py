"""Writer for ZKTeco/NGteco binary `department.dat` files."""

from __future__ import annotations

from pathlib import Path

from lgus_dat.domain.department import Department

RECORD_SIZE = 49
NAME_OFFSET = 1
NAME_SIZE = 48


def _encode_name(name: str) -> bytes:
    return name.encode("latin-1", errors="replace")[:NAME_SIZE]


def _default_record(department_id: int, name: str) -> bytes:
    record = bytearray(RECORD_SIZE)
    record[0] = department_id
    name_bytes = _encode_name(name)
    record[NAME_OFFSET : NAME_OFFSET + len(name_bytes)] = name_bytes
    return bytes(record)


def _update_record(record: bytes, department_id: int, name: str) -> bytes:
    updated = bytearray(record)
    updated[0] = department_id
    updated[NAME_OFFSET : NAME_OFFSET + NAME_SIZE] = b"\x00" * NAME_SIZE
    name_bytes = _encode_name(name)
    updated[NAME_OFFSET : NAME_OFFSET + len(name_bytes)] = name_bytes
    return bytes(updated)


def write_department_dat(departments: list[Department], path: Path) -> None:
    """Write a list of Department records to a binary `department.dat` file.

    If the department was originally imported with a `raw_record`, the writer
    preserves the unknown bytes and updates only the ID and name. New
    departments are written using a default 49-byte record template.
    """
    with path.open("wb") as f:
        for department in departments:
            if department.raw_record:
                record = _update_record(
                    department.raw_record, department.department_id, department.name
                )
            else:
                record = _default_record(department.department_id, department.name)
            f.write(record)
