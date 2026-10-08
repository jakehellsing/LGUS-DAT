"""Tests for the DTR-level CSV writer (one row per employee per day)."""

import csv
from datetime import date, datetime
from pathlib import Path

from lgus_dat.domain.attendance_record import AttendanceRecord, PunchStatus
from lgus_dat.output.dtr_csv_writer import DTR_CSV_FIELDNAMES, write_dtr_csv

# October 2026: Oct 1 = Thursday, Oct 3-4 = Sat/Sun, Oct 5 = Monday.
MONTH = date(2026, 10, 1)


def _make_record(
    employee_id: str,
    day: int,
    punch_time: str,
    status: PunchStatus,
) -> AttendanceRecord:
    hour, minute, second = (int(p) for p in punch_time.split(":"))
    return AttendanceRecord(
        employee_id=employee_id,
        punch_date=date(2026, 10, day),
        punch_time=punch_time,
        timestamp=datetime(2026, 10, day, hour, minute, second),
        status=status,
        original_record=f"{employee_id} 2026-10-{day:02d} {punch_time} 1 0 15 0",
    )


def _read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _row_for(rows: list[dict], employee_id: str, day: int) -> dict:
    target = date(2026, 10, day).isoformat()
    for row in rows:
        if row["Employee ID"] == employee_id and row["Date"] == target:
            return row
    raise AssertionError(f"no row for employee {employee_id} on {target}")


def test_writes_header_and_one_row_per_day(tmp_path: Path) -> None:
    output = tmp_path / "dtr.csv"
    rows_written = write_dtr_csv({"1": []}, MONTH, output)

    assert rows_written == 31
    rows = _read_rows(output)
    assert rows[0].keys() == dict.fromkeys(DTR_CSV_FIELDNAMES).keys()
    assert len(rows) == 31
    assert rows[0]["Date"] == "2026-10-01"
    assert rows[-1]["Date"] == "2026-10-31"


def test_four_punch_day_maps_to_slots(tmp_path: Path) -> None:
    records = [
        _make_record("1", 5, "08:00:00", PunchStatus.IN),
        _make_record("1", 5, "12:00:00", PunchStatus.OUT),
        _make_record("1", 5, "13:00:00", PunchStatus.IN),
        _make_record("1", 5, "17:00:00", PunchStatus.OUT),
    ]
    output = tmp_path / "dtr.csv"
    write_dtr_csv(
        {"1": records},
        MONTH,
        output,
        employee_names={"1": "Doe, John"},
    )

    row = _row_for(_read_rows(output), "1", 5)
    assert row["Employee Name"] == "Doe, John"
    assert row["AM Arrival"] == "08:00"
    assert row["AM Departure"] == "12:00"
    assert row["PM Arrival"] == "13:00"
    assert row["PM Departure"] == "17:00"
    assert row["Undertime Hr"] == ""
    assert row["Undertime Min"] == ""
    assert row["Remarks"] == "MON"


def test_slot_override_is_applied(tmp_path: Path) -> None:
    records = [
        _make_record("1", 6, "08:00:00", PunchStatus.IN),
        _make_record("1", 6, "12:00:00", PunchStatus.OUT),
        _make_record("1", 6, "13:00:00", PunchStatus.IN),
        _make_record("1", 6, "17:00:00", PunchStatus.OUT),
    ]
    output = tmp_path / "dtr.csv"
    write_dtr_csv(
        {"1": records},
        MONTH,
        output,
        dtr_overrides={"1": {date(2026, 10, 6): {"out_pm": "18:30:00"}}},
    )

    row = _row_for(_read_rows(output), "1", 6)
    assert row["PM Departure"] == "18:30"


def test_holiday_and_filing_combine_in_remarks(tmp_path: Path) -> None:
    output = tmp_path / "dtr.csv"
    write_dtr_csv(
        {"1": []},
        MONTH,
        output,
        month_holidays={7: "Special Holiday"},
        employee_status={"1": {7: ["Sick Leave"], 8: ["Vacation Leave"]}},
    )

    rows = _read_rows(output)
    assert _row_for(rows, "1", 7)["Remarks"] == "Special Holiday / Sick Leave"
    assert _row_for(rows, "1", 8)["Remarks"] == "Vacation Leave"
    assert _row_for(rows, "1", 9)["Remarks"] == "FRI"


def test_undertime_rules(tmp_path: Path) -> None:
    # Oct 5 (Mon): no punches -> 8 hr undertime.
    # Oct 6 (Tue): arrival 08:05 with otherwise complete day -> 5 min undertime.
    # Oct 7 (Wed): filed leave -> no undertime.
    # Oct 3 (Sat): weekend -> no undertime.
    records = [
        _make_record("1", 6, "08:05:00", PunchStatus.IN),
        _make_record("1", 6, "12:00:00", PunchStatus.OUT),
        _make_record("1", 6, "13:00:00", PunchStatus.IN),
        _make_record("1", 6, "17:00:00", PunchStatus.OUT),
    ]
    output = tmp_path / "dtr.csv"
    write_dtr_csv(
        {"1": records},
        MONTH,
        output,
        employee_status={"1": {7: ["Sick Leave"]}},
    )

    rows = _read_rows(output)

    monday = _row_for(rows, "1", 5)
    assert monday["Undertime Hr"] == "8"
    assert monday["Undertime Min"] == "0"

    tuesday = _row_for(rows, "1", 6)
    assert tuesday["Undertime Hr"] == "0"
    assert tuesday["Undertime Min"] == "5"

    filed_day = _row_for(rows, "1", 7)
    assert filed_day["Undertime Hr"] == ""
    assert filed_day["Undertime Min"] == ""

    saturday = _row_for(rows, "1", 3)
    assert saturday["Undertime Hr"] == ""
    assert saturday["Undertime Min"] == ""


def test_zero_punch_employee_emits_all_days(tmp_path: Path) -> None:
    output = tmp_path / "dtr.csv"
    rows_written = write_dtr_csv({"99": []}, MONTH, output)

    assert rows_written == 31
    rows = _read_rows(output)
    assert all(row["Employee ID"] == "99" for row in rows)
    assert all(
        row["AM Arrival"] == ""
        and row["AM Departure"] == ""
        and row["PM Arrival"] == ""
        and row["PM Departure"] == ""
        for row in rows
    )


def test_employees_sorted_by_id_then_days_ascending(tmp_path: Path) -> None:
    records = {
        "2": [_make_record("2", 5, "08:00:00", PunchStatus.IN)],
        "1": [_make_record("1", 5, "08:00:00", PunchStatus.IN)],
    }
    output = tmp_path / "dtr.csv"
    write_dtr_csv(records, MONTH, output)

    rows = _read_rows(output)
    keys = [(row["Employee ID"], row["Day"]) for row in rows]
    assert keys == sorted(keys, key=lambda k: (k[0], int(k[1])))
    assert keys[0] == ("1", "1")
    assert keys[31] == ("2", "1")
