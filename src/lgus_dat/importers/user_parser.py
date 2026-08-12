"""Parser for ZKTeco/NGteco binary `user.dat` employee master files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from lgus_dat.domain.employee import Employee


@dataclass(frozen=True, slots=True)
class UserDatParseError:
    """Error encountered while parsing a user.dat record."""

    record_index: int
    reason: str

    def __str__(self) -> str:
        return f"Record {self.record_index}: {self.reason}"


def parse_user_dat(path: Path, record_size: int = 72) -> tuple[list[Employee], list[UserDatParseError]]:
    """Parse a `user.dat` binary export into Employee records.

    The observed format (72-byte fixed records):
      - byte 0: device user id (integer)
      - bytes 1-10: header / flags / name length
      - bytes 11-34: name, null-padded
      - bytes 35-71: remaining fields (privilege, string id, card no, etc.)
    """
    employees: list[Employee] = []
    errors: list[UserDatParseError] = []

    raw = path.read_bytes()
    if len(raw) % record_size != 0:
        errors.append(
            UserDatParseError(
                0,
                f"File length ({len(raw)}) is not a multiple of record size ({record_size})",
            )
        )

    for index in range(0, len(raw), record_size):
        record = raw[index : index + record_size]
        if len(record) < 11:
            errors.append(UserDatParseError(index // record_size, "Record too short"))
            continue

        user_id = str(record[0])
        name_bytes = record[11:].split(b"\x00")[0]
        try:
            name = name_bytes.decode("utf-8", errors="replace").strip()
        except UnicodeDecodeError:
            name = name_bytes.decode("latin-1", errors="replace").strip()

        employees.append(Employee(device_user_id=user_id, name=name))

    return employees, errors
