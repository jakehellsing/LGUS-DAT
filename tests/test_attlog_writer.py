"""Tests for attlog.dat writer."""

from datetime import date, datetime
from pathlib import Path

from lgus_dat.domain.attendance_record import AttendanceRecord, PunchStatus
from lgus_dat.output.attlog_writer import write_attlog


def _make_record(employee_id: str, status: PunchStatus, original: str) -> AttendanceRecord:
    return AttendanceRecord(
        employee_id=employee_id,
        punch_date=date(2026, 8, 12),
        punch_time="08:00:00",
        timestamp=datetime(2026, 8, 12, 8, 0, 0),
        status=status,
        original_record=original,
    )


def test_write_attlog_preserves_format_and_updates_status(tmp_path: Path) -> None:
    records = [
        _make_record("2", PunchStatus.IN, "2 2026-08-12 08:03:27 1 0 15 0"),
        _make_record("13", PunchStatus.OUT, "13 2026-08-12 09:32:07 1 1 15 0"),
    ]
    output = tmp_path / "processed_attlog.dat"
    write_attlog(records, output)

    lines = [line for line in output.read_text(encoding="utf-8").splitlines() if line]
    assert len(lines) == 2
    # IN -> status 0
    assert "\t2026-08-12 08:00:00\t1\t0\t15\t0" in lines[0]
    # OUT -> status 1
    assert "\t2026-08-12 08:00:00\t1\t1\t15\t0" in lines[1]


def test_write_attlog_defaults_missing_fields(tmp_path: Path) -> None:
    record = _make_record("5", PunchStatus.IN, "5 2026-08-12 08:00:00")
    output = tmp_path / "out.dat"
    write_attlog([record], output)
    lines = [line for line in output.read_text(encoding="utf-8").splitlines() if line]
    assert lines[0] == "5\t2026-08-12 08:00:00\t1\t0\t0\t0"


def test_write_attlog_preserves_original_id_padding(tmp_path: Path) -> None:
    record = _make_record("44", PunchStatus.OUT, "       44 2026-08-12 20:28:44 1 0 1 0")
    output = tmp_path / "out.dat"
    write_attlog([record], output)
    lines = [line for line in output.read_text(encoding="utf-8").splitlines() if line]
    assert lines[0] == "       44\t2026-08-12 08:00:00\t1\t1\t1\t0"
