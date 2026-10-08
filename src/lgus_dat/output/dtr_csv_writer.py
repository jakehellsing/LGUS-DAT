"""Write a generated monthly DTR to CSV, one row per employee per day.

Emits the same computed DTR data shown in the PDF report and the Daily DTR
Review preview: AM/PM time slots with manual slot overrides applied, the
Remarks column (holiday and filed-status labels), and computed undertime.
"""

from __future__ import annotations

import calendar
import csv
from datetime import date
from pathlib import Path
from typing import Optional

from lgus_dat.domain.attendance_record import AttendanceRecord
from lgus_dat.output.pdf_writer import (
    DailyPunches,
    _calculate_undertime,
    _format_time,
    _map_punches_to_daily_slots,
    _remark,
)

DTR_CSV_FIELDNAMES = [
    "Employee ID",
    "Employee Name",
    "Date",
    "Day",
    "AM Arrival",
    "AM Departure",
    "PM Arrival",
    "PM Departure",
    "Undertime Hr",
    "Undertime Min",
    "Remarks",
]


def write_dtr_csv(
    employee_records: dict[str, list[AttendanceRecord]],
    month: date,
    output_path: Path,
    employee_names: Optional[dict[str, str]] = None,
    month_holidays: Optional[dict[int, str]] = None,
    employee_status: Optional[dict[str, dict[int, list[str]]]] = None,
    dtr_overrides: Optional[dict[str, dict[date, dict[str, str]]]] = None,
) -> int:
    """Write a DTR-style CSV for the given month.

    Args:
        employee_records: Dictionary mapping employee_id to attendance records
        month: The month to export (day component is ignored)
        output_path: Path where the CSV file will be saved
        employee_names: Optional mapping of employee_id to display name
        month_holidays: Optional mapping of day-of-month to holiday name
        employee_status: Optional mapping of employee_id to day-of-month to
            list of filed status labels
        dtr_overrides: Optional mapping of employee_id to date to slot overrides

    Returns:
        Number of data rows written
    """
    holidays_by_day = month_holidays or {}
    status_by_employee = employee_status or {}
    overrides_by_employee = dtr_overrides or {}

    _, num_days = calendar.monthrange(month.year, month.month)
    rows_written = 0

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DTR_CSV_FIELDNAMES)
        writer.writeheader()

        for employee_id in sorted(employee_records.keys()):
            daily_punches = _map_punches_to_daily_slots(
                employee_records[employee_id],
                month,
                overrides_by_employee.get(employee_id),
            )
            employee_status_by_day = status_by_employee.get(employee_id, {})
            employee_name = (
                employee_names.get(employee_id) if employee_names else None
            ) or ""

            for day in range(1, num_days + 1):
                punches = daily_punches.get(day, DailyPunches(day=day))
                day_statuses = employee_status_by_day.get(day, [])
                undertime_hr, undertime_min = _calculate_undertime(
                    month.year,
                    month.month,
                    day,
                    punches,
                    day_statuses,
                    holidays_by_day,
                )
                remark = _remark(
                    month.year,
                    month.month,
                    day,
                    holidays_by_day,
                    employee_status_by_day,
                )

                writer.writerow(
                    {
                        "Employee ID": employee_id,
                        "Employee Name": employee_name,
                        "Date": date(month.year, month.month, day).isoformat(),
                        "Day": str(day),
                        "AM Arrival": _format_time(punches.in_am),
                        "AM Departure": _format_time(punches.out_am),
                        "PM Arrival": _format_time(punches.in_pm),
                        "PM Departure": _format_time(punches.out_pm),
                        "Undertime Hr": str(undertime_hr) if undertime_hr or undertime_min else "",
                        "Undertime Min": str(undertime_min) if undertime_hr or undertime_min else "",
                        "Remarks": remark,
                    }
                )
                rows_written += 1

    return rows_written
