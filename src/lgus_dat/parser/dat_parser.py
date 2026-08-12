"""Parser for raw MB10-VL .DAT attendance exports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ParsedRecord:
    """Raw record extracted from a .DAT file line."""

    employee_id: str
    timestamp: datetime
    original_line: str
    fields: tuple[str, ...]


class ParseError:
    """Description of a malformed line."""

    def __init__(self, line_number: int, raw_line: str, reason: str) -> None:
        self.line_number = line_number
        self.raw_line = raw_line
        self.reason = reason

    def __str__(self) -> str:
        return f"Line {self.line_number}: {self.reason}\n{self.raw_line}"


def parse_dat_file(path: Path) -> tuple[list[ParsedRecord], list[ParseError]]:
    """Parse a whitespace-delimited .DAT export.

    Expected minimum fields: employee_id, date, time, followed by extra fields.
    Date and time are combined into a single timestamp.
    """
    records: list[ParsedRecord] = []
    errors: list[ParseError] = []

    with path.open("r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue

            fields = line.split()
            if len(fields) < 3:
                errors.append(
                    ParseError(line_number, raw_line, "Too few fields")
                )
                continue

            employee_id = fields[0]
            timestamp_str = f"{fields[1]} {fields[2]}"
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except ValueError as exc:
                errors.append(
                    ParseError(line_number, raw_line, f"Invalid timestamp: {exc}")
                )
                continue

            records.append(
                ParsedRecord(
                    employee_id=employee_id,
                    timestamp=timestamp,
                    original_line=raw_line.rstrip("\n"),
                    fields=tuple(fields),
                )
            )

    return records, errors
