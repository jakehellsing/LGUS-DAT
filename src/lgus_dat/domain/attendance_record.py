"""Domain models for processed attendance records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional


class PunchStatus(str, Enum):
    IN = "IN"
    OUT = "OUT"


@dataclass(frozen=True, slots=True)
class AttendanceRecord:
    """A processed attendance punch with assigned IN/OUT status."""

    employee_id: str
    punch_date: date
    punch_time: str
    timestamp: datetime
    status: PunchStatus
    original_record: str
    exception_flag: Optional[str] = None
    employee_name: Optional[str] = None
