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
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
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


def _create_employee_page(
    employee_id: str,
    employee_name: Optional[str],
    month: date,
    daily_punches: dict[int, DailyPunches],
    department_name: Optional[str] = None,
) -> list:
    """Create PDF elements for one employee's monthly DTR page."""
    elements = []
    
    # Get days in month
    _, num_days = calendar.monthrange(month.year, month.month)
    
    # Build table data
    table_data = [
        ["Day", "Time IN A.M.", "Time OUT A.M.", "Time IN P.M.", "Time OUT P.M."]
    ]
    
    for day in range(1, num_days + 1):
        punches = daily_punches.get(day, DailyPunches(day=day))
        row = [
            str(day),
            punches.in_am or "",
            punches.out_am or "",
            punches.in_pm or "",
            punches.out_pm or "",
        ]
        table_data.append(row)
    
    # Create table
    table = Table(table_data, colWidths=[0.8*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    
    # Style the table
    table.setStyle(
        TableStyle([
            # Header styling
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            
            # Data row styling
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),  # Day column centered
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),  # Time columns centered
            ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
            
            # Grid lines
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.black),  # Thicker header line
            
            # Row striping for readability
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ])
    )
    
    elements.append(table)
    
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