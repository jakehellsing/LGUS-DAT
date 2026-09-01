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
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
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


def _create_employee_page(
    employee_id: str,
    employee_name: Optional[str],
    month: date,
    daily_punches: dict[int, DailyPunches],
    department_name: Optional[str] = None,
) -> list:
    """Create PDF elements for one employee's monthly DTR page."""
    elements = []
    _, num_days = calendar.monthrange(month.year, month.month)

    display_name = employee_name or employee_id
    month_str = month.strftime("%B %Y")

    # Title
    title_table = Table(
        [["DAILY TIME RECORD"]],
        colWidths=[7 * inch],
        style=TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 16),
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ]
        ),
    )
    elements.append(title_table)
    elements.append(Spacer(1, 0.15 * inch))

    # Employee info header
    info_data = [
        ["NAME:", display_name, "For the Month of:", month_str],
        ["Official Hours for Arrival & Departure:", "", "Classes schedules:", ""],
    ]
    info_table = Table(
        info_data,
        colWidths=[1.9 * inch, 1.7 * inch, 1.5 * inch, 1.9 * inch],
        style=TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LINEBELOW", (1, 0), (1, 0), 0.5, colors.black),
                ("LINEBELOW", (3, 0), (3, 0), 0.5, colors.black),
                ("LINEBELOW", (1, 1), (1, 1), 0.5, colors.black),
                ("LINEBELOW", (3, 1), (3, 1), 0.5, colors.black),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        ),
    )
    elements.append(info_table)
    elements.append(Spacer(1, 0.15 * inch))

    # DTR table
    table_data = [
        ["Day", "AM", "", "PM", "", "Remarks"],
        ["", "Arrival", "Departure", "Arrival", "Departure", ""],
    ]

    present_days = 0
    for day in range(1, num_days + 1):
        punches = daily_punches.get(day, DailyPunches(day=day))
        if any((punches.in_am, punches.out_am, punches.in_pm, punches.out_pm)):
            present_days += 1
        row = [
            str(day),
            _format_time(punches.in_am),
            _format_time(punches.out_am),
            _format_time(punches.in_pm),
            _format_time(punches.out_pm),
            _day_name(month.year, month.month, day),
        ]
        table_data.append(row)

    table_data.append(["TOTAL =", "", "", "", "", str(present_days)])

    dtr_table = Table(
        table_data,
        colWidths=[0.5 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 0.95 * inch],
    )

    dtr_table.setStyle(
        TableStyle(
            [
                # Header spanning
                ("SPAN", (0, 0), (0, 1)),
                ("SPAN", (1, 0), (2, 0)),
                ("SPAN", (3, 0), (4, 0)),
                ("SPAN", (5, 0), (5, 1)),
                # Header styling
                ("BACKGROUND", (0, 0), (-1, 1), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 1), 9),
                ("ALIGN", (0, 0), (-1, 1), "CENTER"),
                ("VALIGN", (0, 0), (-1, 1), "MIDDLE"),
                # Data rows
                ("FONTNAME", (0, 2), (-1, -2), "Helvetica"),
                ("FONTSIZE", (0, 2), (-1, -2), 8),
                ("ALIGN", (0, 2), (-1, -2), "CENTER"),
                ("VALIGN", (0, 2), (-1, -2), "MIDDLE"),
                # Total row
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, -1), (-1, -1), 9),
                ("ALIGN", (0, -1), (-1, -1), "CENTER"),
                ("VALIGN", (0, -1), (-1, -1), "MIDDLE"),
                # Grid and striping
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("LINEBELOW", (0, 1), (-1, 1), 1, colors.black),
                ("ROWBACKGROUNDS", (0, 2), (-1, -2), [colors.white, colors.lightgrey]),
            ]
        )
    )
    elements.append(dtr_table)
    elements.append(Spacer(1, 0.15 * inch))

    # Certification
    cert_style = ParagraphStyle(
        "Cert",
        parent=getSampleStyleSheet()["Normal"],
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
    )
    cert_text = (
        "I CERTIFY on my honor that the above is a true and correct report of the hours of work performed, "
        "record of which was made DAILY at the time of arrival and at the time of departure from office."
    )
    elements.append(Paragraph(cert_text, cert_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Signature block
    sig_data = [
        ["", "Verified as to the prescribed office hours"],
        ["", ""],
        [display_name, ""],
        ["Employee", "Verifying Officer"],
    ]
    sig_table = Table(
        sig_data,
        colWidths=[3.5 * inch, 3.5 * inch],
        style=TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LINEBELOW", (0, 1), (0, 1), 0.5, colors.black),
                ("LINEBELOW", (1, 1), (1, 1), 0.5, colors.black),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        ),
    )
    elements.append(sig_table)

    return elements


def generate_dtr_pdf(
    employee_records: dict[str, list[AttendanceRecord]],
    month: date,
    output_path: Path,
    employee_names: Optional[dict[str, str]] = None,
    department_names: Optional[dict[int, str]] = None,
    employee_departments: Optional[dict[str, int]] = None,
) -> None:
    """Generate a DTR PDF report for employees for a given month.
    
    Args:
        employee_records: Dictionary mapping employee_id to list of attendance records
        month: The month to generate the report for (day will be ignored)
        output_path: Path where the PDF file will be saved
        employee_names: Optional dictionary mapping employee_id to employee name
        department_names: Optional dictionary mapping department_id to department name
        employee_departments: Optional dictionary mapping employee_id to department_id
    """
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
    )
    
    elements = []
    
    # Sort employees by ID for consistent ordering
    sorted_employee_ids = sorted(employee_records.keys())
    
    for i, employee_id in enumerate(sorted_employee_ids):
        records = employee_records[employee_id]
        employee_name = employee_names.get(employee_id) if employee_names else None
        
        # Get department info if available
        dept_name = None
        if employee_departments and department_names:
            dept_id = employee_departments.get(employee_id)
            if dept_id is not None:
                dept_name = department_names.get(dept_id)
        
        # Map punches to daily slots
        daily_punches = _map_punches_to_daily_slots(records, month)
        
        # Create page for this employee
        page_elements = _create_employee_page(
            employee_id=employee_id,
            employee_name=employee_name,
            month=month,
            daily_punches=daily_punches,
            department_name=dept_name,
        )
        
        elements.extend(page_elements)
        
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