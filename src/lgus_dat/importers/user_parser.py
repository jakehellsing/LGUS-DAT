"""Parser for ZKTeco/NGteco binary `user.dat` employee master files."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from lgus_dat.domain.employee import Employee


@dataclass(frozen=True, slots=True)
class UserDatParseError:
    """Error encountered while parsing a user.dat record."""

    record_index: int
    reason: str

    def __str__(self) -> str:
        return f"Record {self.record_index}: {self.reason}"


def _decode_cstr(data: bytes) -> str:
    """Return a Latin-1 decoded C string up to the first null byte."""
    return data.split(b"\x00")[0].decode("latin-1", errors="replace")


def _safe_uid_le(data: bytes) -> int:
    """Read a little-endian 16-bit unsigned integer from the first two bytes."""
    return struct.unpack("<H", data[:2])[0]


def parse_user_dat(path: Path, record_size: int = 72) -> tuple[list[Employee], list[UserDatParseError]]:
    """Parse a `user.dat` binary export into Employee records.

    The observed ZK8 72-byte fixed record layout:
      - bytes 0-1:  internal uid (little-endian u16)
      - byte 2:     privilege / role flags
      - bytes 3-10: password (8 bytes, C string)
      - bytes 11-34: name (24 bytes, C string)
      - bytes 35-38: card number (little-endian u32)
      - byte 39:    constant 0x01
      - bytes 40-46: group id (7 bytes, C string)
      - byte 47:    padding / 0x00
      - bytes 48-71: user id / PIN (24 bytes, C string)
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
        if len(record) < 72:
            errors.append(UserDatParseError(index // record_size, "Record too short"))
            continue

        uid = _safe_uid_le(record[0:2])
        privilege = record[2]
        password = _decode_cstr(record[3:11])
        name = _decode_cstr(record[11:35]).strip()
        card = struct.unpack("<I", record[35:39])[0]
        group_id = _decode_cstr(record[40:47]).strip()
        user_id = _decode_cstr(record[48:72]).strip()

        device_user_id = user_id if user_id else str(uid)

        employees.append(
            Employee(
                device_user_id=device_user_id,
                name=name,
                raw_record=bytes(record),
                uid=uid,
                privilege=privilege,
                password=password,
                group_id=group_id,
                card=card,
            )
        )

    return employees, errors
