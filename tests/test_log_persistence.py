"""Tests for attendance log persistence in the local SQLite DB."""

from datetime import datetime
from pathlib import Path

import pytest

from lgus_dat.parser.dat_parser import ParsedRecord
from lgus_dat.persistence.registry import AttendanceRegistry


@pytest.fixture
def registry(tmp_path: Path) -> AttendanceRegistry:
    return AttendanceRegistry(db_path=tmp_path / "test_registry.db")


def test_import_attendance_logs_counts_new_rows(registry: AttendanceRegistry) -> None:
    records = [
        ParsedRecord(
            employee_id="1",
            timestamp=datetime(2026, 8, 12, 8, 0, 0),
            original_line="1 2026-08-12 08:00:00 0 0 0 0",
            fields=("1", "2026-08-12", "08:00:00", "0", "0", "0", "0"),
        ),
        ParsedRecord(
            employee_id="2",
            timestamp=datetime(2026, 8, 12, 9, 0, 0),
            original_line="2 2026-08-12 09:00:00 0 0 0 0",
            fields=("2", "2026-08-12", "09:00:00", "0", "0", "0", "0"),
        ),
    ]
    count = registry.import_attendance_logs(records, Path("device_a.dat"))
    assert count == 2
    assert registry.count_attendance_logs() == 2


def test_import_attendance_logs_skips_exact_duplicates(registry: AttendanceRegistry) -> None:
    record = ParsedRecord(
        employee_id="1",
        timestamp=datetime(2026, 8, 12, 8, 0, 0),
        original_line="1 2026-08-12 08:00:00 0 0 0 0",
        fields=("1", "2026-08-12", "08:00:00", "0", "0", "0", "0"),
    )
    count1 = registry.import_attendance_logs([record], Path("device_a.dat"))
    count2 = registry.import_attendance_logs([record], Path("device_a.dat"))
    assert count1 == 1
    assert count2 == 0
    assert registry.count_attendance_logs() == 1


def test_import_attendance_logs_allows_same_record_from_different_sources(registry: AttendanceRegistry) -> None:
    record = ParsedRecord(
        employee_id="1",
        timestamp=datetime(2026, 8, 12, 8, 0, 0),
        original_line="1 2026-08-12 08:00:00 0 0 0 0",
        fields=("1", "2026-08-12", "08:00:00", "0", "0", "0", "0"),
    )
    registry.import_attendance_logs([record], Path("device_a.dat"))
    registry.import_attendance_logs([record], Path("device_b.dat"))
    assert registry.count_attendance_logs() == 2
    assert set(registry.get_attendance_log_sources()) == {"device_a.dat", "device_b.dat"}


def test_get_attendance_logs_reconstructs_records(registry: AttendanceRegistry) -> None:
    records = [
        ParsedRecord(
            employee_id="1",
            timestamp=datetime(2026, 8, 12, 8, 0, 0),
            original_line="1 2026-08-12 08:00:00 0 0 0 0",
            fields=("1", "2026-08-12", "08:00:00", "0", "0", "0", "0"),
        ),
    ]
    registry.import_attendance_logs(records, Path("device.dat"))
    stored = registry.get_attendance_logs()
    assert len(stored) == 1
    assert stored[0].employee_id == "1"
    assert stored[0].timestamp == datetime(2026, 8, 12, 8, 0, 0)
    assert stored[0].original_line == records[0].original_line
    assert stored[0].fields == records[0].fields
