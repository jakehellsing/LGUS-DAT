"""Generate DTR (Daily Time Record) PDF reports for employees.

Creates monthly attendance reports with an excel-like table format:
- Column 1: Day (1-31)
- Column 2: Time IN A.M.
- Column 3: Time OUT A.M.  
- Column 4: Time IN P.M.
- Column 5: Time OUT P.M.

Each employee gets one page per month. Duplicate punches with the same
timestamp are handled by keeping the first occurrence only.
"""

from __future__ import annotations

import calendar
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Table,
    TableStyle,
)

from lgus_dat.domain.attendance_record import AttendanceRecord, PunchStatus


@dataclass
class DailyPunches:
    """Punch data for a single day with exactly 4 time slots."""
    day: int
    in_am: Optional[str] = None
    out_am: Optional[str] = None
    in_pm: Optional[str] = None
    out_pm: Optional[str] = None


def _remove_duplicate_punches(records: list[AttendanceRecord]) -> list[AttendanceRecord]:
    """Remove duplicate records with the same employee_id, date, and timestamp.
    
    Keeps the first occurrence when duplicates are found.
    """
    seen = set()
    unique_records = []
    
    for record in records:
        key = (record.employee_id, record.punch_date, record.timestamp)
        if key not in seen:
            seen.add(key)
            unique_records.append(record)
    
    return unique_records


def _map_punches_to_daily_slots(
    records: list[AttendanceRecord],
    target_month: date,
) -> dict[int, DailyPunches]:
    """Map attendance records to daily time slots for a given month.
    
    Args:
        records: List of attendance records for one employee
        target_month: The month to generate the report for (day will be ignored)
    
    Returns:
        Dictionary mapping day number (1-31) to DailyPunches data
    """
    # Filter records for the target month
    month_records = [
        r for r in records 
        if r.punch_date.year == target_month.year 
        and r.punch_date.month == target_month.month
    ]
    
    # Remove duplicates
    month_records = _remove_duplicate_punches(month_records)
    
    # Group by day and sort by timestamp
    daily_records: dict[int, list[AttendanceRecord]] = defaultdict(list)
    for record in month_records:
        daily_records[record.punch_date.day].append(record)
    
    # Sort records within each day by timestamp
    for day in daily_records:
        daily_records[day].sort(key=lambda r: r.timestamp)
    
    # Map to the 4 time slots
    daily_punches: dict[int, DailyPunches] = {}
    for day, day_records in daily_records.items():
        punches = DailyPunches(day=day)
        
        # Map first 4 punches to slots (if available)
        for i, record in enumerate(day_records[:4]):
            time_str = record.punch_time  # HH:MM:SS format
            if i == 0:
                punches.in_am = time_str
            elif i == 1:
                punches.out_am = time_str
            elif i == 2:
                punches.in_pm = time_str
            elif i == 3:
                punches.out_pm = time_str
        
        daily_punches[day] = punches
    
    return daily_punches


def _format_time(time_str: Optional[str]) -> str:
    """Format a HH:MM:SS time string as HH:MM for the DTR."""
    if not time_str:
        return ""
    if len(time_str) >= 5 and time_str[2] == ":":
        return time_str[:5]
    return time_str


def _day_name(year: int, month: int, day: int) -> str:
    """Return the abbreviated weekday name (e.g., MON, TUE)."""
    return date(year, month, day).strftime("%a").upper()


def _remark(
    year: int,
    month: int,
    day: int,
    holidays_by_day: dict[int, str],
    employee_status_by_day: dict[int, list[str]],
) -> str:
    """Return the DTR Remarks text for a day.

    If a system-wide holiday or employee filed status exists, show those
    labels; otherwise fall back to the abbreviated weekday.
    """
    parts: list[str] = []
    if day in holidays_by_day:
        parts.append(holidays_by_day[day])

    seen: set[str] = set(parts)
    for status in employee_status_by_day.get(day, []):
        if status not in seen:
            parts.append(status)
            seen.add(status)

    if parts:
        return " / ".join(parts)
    return _day_name(year, month, day)


_OFFICIAL_START = time(8, 0)
_OFFICIAL_LUNCH_OUT = time(12, 0)
_OFFICIAL_LUNCH_IN = time(13, 0)
_OFFICIAL_END = time(17, 0)
_OFFICIAL_WORKDAY_MINUTES = 8 * 60  # 480


def _parse_hhmmss(time_str: Optional[str]) -> Optional[time]:
    """Parse a HH:MM:SS string into a time object."""
    if not time_str:
        return None
    try:
        return datetime.strptime(time_str, "%H:%M:%S").time()
    except ValueError:
        return None


def _minutes_between(start: time, end: time) -> int:
    """Return the whole minutes between two time objects."""
    start_td = timedelta(hours=start.hour, minutes=start.minute, seconds=start.second)
    end_td = timedelta(hours=end.hour, minutes=end.minute, seconds=end.second)
    return int((end_td - start_td).total_seconds() // 60)


def _has_any_punches(punches: DailyPunches) -> bool:
    """Return True if any time slot has a punch."""
    return any(
        (punches.in_am, punches.out_am, punches.in_pm, punches.out_pm)
    )


def _calculate_undertime(
    year: int,
    month: int,
    day: int,
    punches: DailyPunches,
    status_labels: list[str] | None = None,
) -> tuple[int, int]:
    """Calculate daily undertime in minutes against the government DTR schedule.

    Official weekday schedule:
    - 8:00 AM arrival
    - 12:00 PM lunch out
    - 1:00 PM lunch in
    - 5:00 PM departure

    Rules:
    - Undertime is counted only on Monday-Friday.
    - A weekday with no punches at all = 8 hours undertime.
    - Late arrival after 8:00 AM counts.
    - Early lunch out before 12:00 PM counts.
    - Late lunch in after 1:00 PM counts.
    - Early end before 5:00 PM counts.
    - A day filed as `Fieldwork` has no undertime.
    """
    if status_labels and "Fieldwork" in status_labels:
        return 0, 0

    if date(year, month, day).weekday() >= 5:
        return 0, 0

    if not _has_any_punches(punches):
        return _OFFICIAL_WORKDAY_MINUTES // 60, _OFFICIAL_WORKDAY_MINUTES % 60

    total_minutes = 0

    arrival = _parse_hhmmss(punches.in_am)
    if arrival and arrival > _OFFICIAL_START:
        total_minutes += _minutes_between(_OFFICIAL_START, arrival)

    lunch_out = _parse_hhmmss(punches.out_am)
    if lunch_out and lunch_out < _OFFICIAL_LUNCH_OUT:
        total_minutes += _minutes_between(lunch_out, _OFFICIAL_LUNCH_OUT)

    lunch_in = _parse_hhmmss(punches.in_pm)
    if lunch_in and lunch_in > _OFFICIAL_LUNCH_IN:
        total_minutes += _minutes_between(_OFFICIAL_LUNCH_IN, lunch_in)

    # Use the last available departure (PM first, then AM fallback for 2-punch days).
    departure_str = punches.out_pm or punches.out_am
    departure = _parse_hhmmss(departure_str)
    if departure and departure < _OFFICIAL_END:
        total_minutes += _minutes_between(departure, _OFFICIAL_END)

    return total_minutes // 60, total_minutes % 60


def _create_employee_page(
    employee_id: str,
    employee_name: Optional[str],
    month: date,
    daily_punches: dict[int, DailyPunches],
    department_name: Optional[str] = None,
    employee_position: Optional[str] = None,
    department_head_name: Optional[str] = None,
    department_head_position: Optional[str] = None,
    page_width: float = 3.7 * inch,
    holidays_by_day: dict[int, str] | None = None,
    employee_status_by_day: dict[int, list[str]] | None = None,
) -> Table:
    """Create a single-column DTR table that fits inside a two-column layout."""
    _, num_days = calendar.monthrange(month.year, month.month)

    holidays_by_day = holidays_by_day or {}
    employee_status_by_day = employee_status_by_day or {}

    display_name = employee_name or employee_id
    month_str = month.strftime("%B %Y")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DTRTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
    )
    cert_style = ParagraphStyle(
        "Cert",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        alignment=TA_CENTER,
    )
    info_style = ParagraphStyle(
        "Info",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
    )
    sig_style = ParagraphStyle(
        "Sig",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        alignment=TA_CENTER,
    )
    remark_style = ParagraphStyle(
        "Remark",
        parent=styles["Normal"],
        fontSize=6,
        leading=7,
        alignment=TA_CENTER,
    )
    cert_text = (
        "I CERTIFY on my honor that the above is a true and correct report of the hours of work performed, "
        "record of which was made DAILY at the time of arrival and at the time of departure from office."
    )

    # Title
    title_para = Paragraph("DAILY TIME RECORD", title_style)

    # Employee info header
    label_width = 0.85 * inch
    info_data = [
        [Paragraph("NAME:", info_style), Paragraph(display_name, info_style)],
    ]
    if employee_position:
        info_data.append([Paragraph("POSITION:", info_style), Paragraph(employee_position, info_style)])
    info_data.append([Paragraph("For the Month of:", info_style), Paragraph(month_str, info_style)])
    line_style_commands = [
        ("LINEBELOW", (1, row - 1), (1, row - 1), 0.5, colors.black)
        for row in range(1, len(info_data) + 1)
    ]
    info_table = Table(
        info_data,
        colWidths=[label_width, page_width - label_width],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                *line_style_commands,
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        ),
    )

    # DTR table
    table_data = [
        ["Day", "AM", "", "PM", "", "Undertime", "", "Remarks"],
        ["", "Arrival", "Departure", "Arrival", "Departure", "Hr", "Min", ""],
    ]

    total_undertime_hr = 0
    total_undertime_min = 0
    for day in range(1, num_days + 1):
        punches = daily_punches.get(day, DailyPunches(day=day))
        day_statuses = employee_status_by_day.get(day, [])
        undertime_hr, undertime_min = _calculate_undertime(
            month.year, month.month, day, punches, day_statuses
        )
        total_undertime_hr += undertime_hr
        total_undertime_min += undertime_min
        remark = _remark(
            month.year,
            month.month,
            day,
            holidays_by_day,
            employee_status_by_day,
        )
        remark_cell = Paragraph(remark, remark_style) if holidays_by_day or employee_status_by_day else remark
        row = [
            str(day),
            _format_time(punches.in_am),
            _format_time(punches.out_am),
            _format_time(punches.in_pm),
            _format_time(punches.out_pm),
            str(undertime_hr) if undertime_hr or undertime_min else "",
            str(undertime_min) if undertime_hr or undertime_min else "",
            remark_cell,
        ]
        table_data.append(row)

    table_data.append(
        ["TOTAL =", "", "", "", "", str(total_undertime_hr), str(total_undertime_min), ""]
    )

    base_dtr_width = 3.7 * inch
    base_col_widths = [
        0.3 * inch,
        0.52 * inch,
        0.52 * inch,
        0.52 * inch,
        0.52 * inch,
        0.33 * inch,
        0.33 * inch,
        0.45 * inch,
    ]
    scale = page_width / base_dtr_width
    dtr_col_widths = [w * scale for w in base_col_widths]

    dtr_table = Table(table_data, colWidths=dtr_col_widths)

    dtr_table.setStyle(
        TableStyle(
            [
                # Header spanning
                ("SPAN", (0, 0), (0, 1)),
                ("SPAN", (1, 0), (2, 0)),
                ("SPAN", (3, 0), (4, 0)),
                ("SPAN", (5, 0), (6, 0)),
                ("SPAN", (7, 0), (7, 1)),
                # Header styling
                ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 1), 7),
                ("ALIGN", (0, 0), (-1, 1), "CENTER"),
                ("VALIGN", (0, 0), (-1, 1), "MIDDLE"),
                # Data rows
                ("FONTNAME", (0, 2), (-1, -2), "Helvetica"),
                ("FONTSIZE", (0, 2), (-1, -2), 7),
                ("ALIGN", (0, 2), (-1, -2), "CENTER"),
                ("VALIGN", (0, 2), (-1, -2), "MIDDLE"),
                ("TOPPADDING", (0, 2), (-1, -2), 1),
                ("BOTTOMPADDING", (0, 2), (-1, -2), 1),
                # Total row
                ("SPAN", (0, -1), (4, -1)),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, -1), (-1, -1), 8),
                ("ALIGN", (0, -1), (-1, -1), "CENTER"),
                ("VALIGN", (0, -1), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, -1), (4, -1), "LEFT"),
                # Grid
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("LINEBELOW", (0, 1), (-1, 1), 1, colors.black),
            ]
        )
    )

    # Signature block
    verifying_officer_name = department_head_name or ""
    verifying_officer_position = department_head_position or "Verifying Officer"
    sig_data = [
        [""],
        [Paragraph(display_name, sig_style)],
        [Paragraph("Employee", sig_style)],
        [""],
        [Paragraph("Verified as to the prescribed office hours", sig_style)],
        [Paragraph(verifying_officer_name, sig_style)],
        [Paragraph(verifying_officer_position, sig_style)],
    ]
    sig_table = Table(
        sig_data,
        colWidths=[page_width],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (0, 0), 0.5, colors.black),
                ("LINEBELOW", (0, 5), (0, 5), 0.5, colors.black),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        ),
    )

    # Combine into one vertical table
    page_data = [
        [title_para],
        [info_table],
        [dtr_table],
        [Paragraph(cert_text, cert_style)],
        [sig_table],
    ]
    page_table = Table(
        page_data,
        colWidths=[page_width],
        style=TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        ),
    )

    return page_table


def generate_dtr_pdf(
    employee_records: dict[str, list[AttendanceRecord]],
    month: date,
    output_path: Path,
    employee_names: Optional[dict[str, str]] = None,
    department_names: Optional[dict[int, str]] = None,
    employee_departments: Optional[dict[str, int]] = None,
    employee_positions: Optional[dict[str, str]] = None,
    department_heads: Optional[dict[int, str]] = None,
    department_head_positions: Optional[dict[int, str]] = None,
    month_holidays: Optional[dict[int, str]] = None,
    employee_status: Optional[dict[str, dict[int, list[str]]]] = None,
) -> None:
    """Generate a DTR PDF report for employees for a given month.

    Args:
        employee_records: Dictionary mapping employee_id to list of attendance records
        month: The month to generate the report for (day will be ignored)
        output_path: Path where the PDF file will be saved
        employee_names: Optional dictionary mapping employee_id to employee name
        department_names: Optional dictionary mapping department_id to department name
        employee_departments: Optional dictionary mapping employee_id to department_id
        employee_positions: Optional dictionary mapping employee_id to position
        department_heads: Optional dictionary mapping department_id to department head name
        department_head_positions: Optional dictionary mapping department_id to department head position
        month_holidays: Optional mapping of day-of-month to holiday name for the month
        employee_status: Optional mapping of employee_id to day-of-month to list of status labels
    """
    holidays_by_day = month_holidays or {}
    status_by_employee = employee_status or {}

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.4*inch,
        leftMargin=0.4*inch,
        topMargin=0.4*inch,
        bottomMargin=0.4*inch,
    )
    
    elements = []

    # Two-column layout: two copies of the same DTR side-by-side on one page
    col_width = (letter[0] - doc.leftMargin - doc.rightMargin - 0.1 * inch) / 2

    # Sort employees by ID for consistent ordering
    sorted_employee_ids = sorted(employee_records.keys())

    for i, employee_id in enumerate(sorted_employee_ids):
        records = employee_records[employee_id]
        employee_name = employee_names.get(employee_id) if employee_names else None

        # Get department info if available
        dept_name = None
        dept_head_name = None
        dept_head_position = None
        if employee_departments and department_names:
            dept_id = employee_departments.get(employee_id)
            if dept_id is not None:
                dept_name = department_names.get(dept_id)
                if department_heads:
                    dept_head_name = department_heads.get(dept_id)
                if department_head_positions:
                    dept_head_position = department_head_positions.get(dept_id)

        employee_position = employee_positions.get(employee_id) if employee_positions else None

        # Map punches to daily slots
        daily_punches = _map_punches_to_daily_slots(records, month)

        employee_status_by_day = status_by_employee.get(employee_id, {})

        # Create two copies of the same DTR page side-by-side
        left_page = _create_employee_page(
            employee_id=employee_id,
            employee_name=employee_name,
            month=month,
            daily_punches=daily_punches,
            department_name=dept_name,
            employee_position=employee_position,
            department_head_name=dept_head_name,
            department_head_position=dept_head_position,
            page_width=col_width,
            holidays_by_day=holidays_by_day,
            employee_status_by_day=employee_status_by_day,
        )
        right_page = _create_employee_page(
            employee_id=employee_id,
            employee_name=employee_name,
            month=month,
            daily_punches=daily_punches,
            department_name=dept_name,
            employee_position=employee_position,
            department_head_name=dept_head_name,
            department_head_position=dept_head_position,
            page_width=col_width,
            holidays_by_day=holidays_by_day,
            employee_status_by_day=employee_status_by_day,
        )

        outer = Table(
            [[left_page, "", right_page]],
            colWidths=[col_width, 0.1 * inch, col_width],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            ),
        )
        elements.append(KeepTogether([outer]))

        # Add page break between employees (except after last employee)
        if i < len(sorted_employee_ids) - 1:
            elements.append(PageBreak())
    
    doc.build(elements)


def group_records_by_employee(records: list[AttendanceRecord]) -> dict[str, list[AttendanceRecord]]:
    """Group attendance records by employee_id."""
    grouped: dict[str, list[AttendanceRecord]] = defaultdict(list)
    for record in records:
        grouped[record.employee_id].append(record)
    return dict(grouped)