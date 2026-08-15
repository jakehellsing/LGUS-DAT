"""Writer for processed attendance data in NGteco/ZKTeco `attlog.dat` format.

The device/text export uses fixed-width fields, tab separators and CRLF line
endings:

    <employee id right-padded to 14 chars>\t<YYYY-MM-DD HH:MM:SS>\t<verify>\t<status>\t<workcode>\t<reserved>\r\n

The writer preserves the original extra device fields and updates the status
column to reflect the computed IN/OUT state:

    IN  -> 0
    OUT -> 1
"""

from __future__ import annotations

from pathlib import Path

from lgus_dat.domain.attendance_record import AttendanceRecord, PunchStatus


def _default_extras(original_record: str) -> tuple[str, str, str, str]:
    """Extract original verify/status/workcode/reserved fields if present."""
    parts = original_record.split()
    if len(parts) >= 7:
        return parts[3], parts[4], parts[5], parts[6]
    # Fallback when the source line is missing trailing device fields.
    return "1", "0", "0", "0"


def _status_to_field(status: PunchStatus, current_value: str) -> str:
    """Map computed status to the numeric state used in attlog exports."""
    if status == PunchStatus.IN:
        return "0"
    if status == PunchStatus.OUT:
        return "1"
    return current_value


def write_attlog(records: list[AttendanceRecord], path: Path) -> None:
    """Write processed records to a tab-delimited `.dat` file.

    The format matches the original NGteco/ZKTeco `attlog.dat` export so the
    resulting file can be consumed by device management software.
    """
    with path.open("w", encoding="utf-8", newline="") as f:
        for rec in records:
            verify, status_field, workcode, reserved = _default_extras(rec.original_record)
            status_field = _status_to_field(rec.status, status_field)
            line = (
                f"{rec.employee_id.rjust(14)}\t"
                f"{rec.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\t"
                f"{verify}\t{status_field}\t{workcode}\t{reserved}\r\n"
            )
            f.write(line)
