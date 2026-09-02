"""Attendance status filing domain model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True, slots=True)
class AttendanceFiling:
    """A per-employee date range filed with an attendance status."""

    employee_id: str
    start_date: date
    end_date: date
    status: str
    filing_id: Optional[int] = None
