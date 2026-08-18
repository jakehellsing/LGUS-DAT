"""Writer for processed attendance data in NGteco/ZKTeco `attlog.dat` format.

The device/text export uses the same ID field formatting as the source file,
with tab separators and CRLF line endings:

    <employee id field as in source>\t<YYYY-MM-DD HH:MM:SS>\t<verify>\t<status>\t<workcode>\t<reserved>\r\n

The writer preserves the original ID padding/width, the original extra device
fields, and updates the status column to reflect the computed IN/OUT state:

    IN  -> 0
    OUT -> 1
"""

from __future__ import annotations

import re
from pathlib import Path

from lgus_dat.domain.attendance_record import AttendanceRecord, PunchStatus


def _format_id_field(original_record: str, employee_id: str) -> str:
    """Preserve the original ID padding/width from the source record.

    The source line begins with the employee ID possibly padded with leading
    spaces. If that prefix is still present, reuse it exactly; otherwise fall
    back to the bare ID.
    """
    pattern = r"^\s*" + re.escape(employee_id) + r"(?=\s)"
    match = re.match(pattern, original_record)
    if match:
        return match.group(0)
    return employee_id


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
            id_field = _format_id_field(rec.original_record, rec.employee_id)
            line = (
                f"{id_field}\t"
                f"{rec.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\t"
                f"{verify}\t{status_field}\t{workcode}\t{reserved}\r\n"
            )
            f.write(line)
