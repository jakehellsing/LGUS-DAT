"""Parser for ZKTeco/NGteco binary `department.dat` files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from lgus_dat.domain.department import Department


@dataclass(frozen=True, slots=True)
class DepartmentParseError:
    """Error encountered while parsing a department.dat record."""

    record_index: int
    reason: str

    def __str__(self) -> str:
        return f"Record {self.record_index}: {self.reason}"


def parse_department_dat(
    path: Path, record_size: int = 49
) -> tuple[list[Department], list[DepartmentParseError]]:
    """Parse a `department.dat` binary export into Department records.

    The observed format (49-byte fixed records):
      - byte 0: department id
      - bytes 1-48: department name, null-padded
    """
    departments: list[Department] = []
    errors: list[DepartmentParseError] = []

    raw = path.read_bytes()
    if len(raw) % record_size != 0:
        errors.append(
            DepartmentParseError(
                0,
                f"File length ({len(raw)}) is not a multiple of record size ({record_size})",
            )
        )

    for index in range(0, len(raw), record_size):
        record = raw[index : index + record_size]
        if len(record) < 2:
            errors.append(DepartmentParseError(index // record_size, "Record too short"))
            continue

        dept_id = record[0]
        name_bytes = record[1:].split(b"\x00")[0]
        try:
            name = name_bytes.decode("utf-8", errors="replace").strip()
        except UnicodeDecodeError:
            name = name_bytes.decode("latin-1", errors="replace").strip()

        departments.append(
            Department(department_id=dept_id, name=name, raw_record=record)
        )

    return departments, errors
