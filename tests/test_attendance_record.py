"""Tests for the AttendanceRecord domain model."""

from dataclasses import replace
from datetime import date, datetime

from lgus_dat.domain.attendance_record import AttendanceRecord, PunchStatus


def test_replace_status_marks_manual_edit() -> None:
    record = AttendanceRecord(
        employee_id="42",
        punch_date=date(2026, 8, 12),
        punch_time="08:00:00",
        timestamp=datetime(2026, 8, 12, 8, 0, 0),
        status=PunchStatus.IN,
        original_record="42\t2026-08-12\t08:00:00\t0\t0\t0\t0",
    )
    edited = replace(record, status=PunchStatus.OUT, exception_flag="MANUAL_EDIT")
    assert edited.status == PunchStatus.OUT
    assert edited.exception_flag == "MANUAL_EDIT"
    assert edited.employee_id == record.employee_id
    assert edited.timestamp == record.timestamp
