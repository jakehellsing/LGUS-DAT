"""Write processed attendance records to CSV."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from lgus_dat.domain.attendance_record import AttendanceRecord


def write_csv(records: Iterable[AttendanceRecord], path: Path) -> None:
    """Write records to a CSV file with the required output columns."""
    fieldnames = [
        "Employee ID",
        "Employee Name",
        "Date",
        "Time",
        "Timestamp",
        "Status",
        "Original Record",
        "Exception Flag",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "Employee ID": record.employee_id,
                    "Employee Name": record.employee_name or "",
                    "Date": record.punch_date.isoformat(),
                    "Time": record.punch_time,
                    "Timestamp": record.timestamp.isoformat(sep=" ", timespec="seconds"),
                    "Status": record.status.value,
                    "Original Record": record.original_record,
                    "Exception Flag": record.exception_flag or "",
                }
            )
