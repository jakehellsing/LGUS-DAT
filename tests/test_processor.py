"""Tests for the MB10-VL .DAT processor core rules."""

from datetime import datetime

from lgus_dat.domain.attendance_record import PunchStatus
from lgus_dat.parser.dat_parser import ParsedRecord, parse_dat_file
from lgus_dat.processing.sequence_processor import assign_status, process_records


def _make_record(employee_id: str, timestamp_str: str, fields: tuple[str, ...] | None = None) -> ParsedRecord:
    ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    return ParsedRecord(
        employee_id=employee_id,
        timestamp=ts,
        original_line=f"{employee_id} {timestamp_str}",
        fields=fields or (employee_id, timestamp_str.split()[0], timestamp_str.split()[1]),
    )


def test_assign_status_alternates_starting_with_in() -> None:
    assert assign_status(0) == PunchStatus.IN
    assert assign_status(1) == PunchStatus.OUT
    assert assign_status(2) == PunchStatus.IN
    assert assign_status(3) == PunchStatus.OUT


def test_two_punches_become_in_out() -> None:
    records = [
        _make_record("1001", "2026-08-12 08:00:00"),
        _make_record("1001", "2026-08-12 17:00:00"),
    ]
    processed = process_records(records)
    assert len(processed) == 2
    assert processed[0].status == PunchStatus.IN
    assert processed[1].status == PunchStatus.OUT


def test_four_punches_alternate() -> None:
    records = [
        _make_record("1001", "2026-08-12 08:00:00"),
        _make_record("1001", "2026-08-12 12:00:00"),
        _make_record("1001", "2026-08-12 13:00:00"),
        _make_record("1001", "2026-08-12 17:00:00"),
    ]
    processed = process_records(records)
    assert [r.status for r in processed] == [
        PunchStatus.IN,
        PunchStatus.OUT,
        PunchStatus.IN,
        PunchStatus.OUT,
    ]


def test_odd_punch_count_flags_unpaired_final_in() -> None:
    records = [
        _make_record("1001", "2026-08-12 08:00:00"),
        _make_record("1001", "2026-08-12 12:00:00"),
        _make_record("1001", "2026-08-12 13:00:00"),
    ]
    processed = process_records(records)
    assert processed[-1].status == PunchStatus.IN
    assert processed[-1].exception_flag == "UNPAIRED_FINAL_IN"


def test_each_employee_starts_with_in() -> None:
    records = [
        _make_record("1", "2026-08-12 08:00:00"),
        _make_record("1", "2026-08-12 12:00:00"),
        _make_record("2", "2026-08-12 08:10:00"),
        _make_record("2", "2026-08-12 12:05:00"),
    ]
    processed = process_records(records)
    by_employee = {eid: list(group) for eid, group in _group_by_employee(processed)}
    assert by_employee["1"][0].status == PunchStatus.IN
    assert by_employee["2"][0].status == PunchStatus.IN


def test_sequence_resets_each_calendar_day() -> None:
    records = [
        _make_record("1001", "2026-08-12 08:00:00"),
        _make_record("1001", "2026-08-12 17:00:00"),
        _make_record("1001", "2026-08-13 08:01:00"),
        _make_record("1001", "2026-08-13 17:01:00"),
    ]
    processed = process_records(records)
    assert processed[2].status == PunchStatus.IN
    assert processed[3].status == PunchStatus.OUT


def test_unsorted_input_is_sorted() -> None:
    records = [
        _make_record("1001", "2026-08-12 17:00:00"),
        _make_record("1001", "2026-08-12 08:00:00"),
        _make_record("1001", "2026-08-12 12:00:00"),
    ]
    processed = process_records(records)
    assert [r.timestamp.strftime("%H:%M") for r in processed] == ["08:00", "12:00", "17:00"]
    assert [r.status for r in processed] == [PunchStatus.IN, PunchStatus.OUT, PunchStatus.IN]


def test_parse_dat_file(tmp_path) -> None:
    dat_file = tmp_path / "attendance.dat"
    dat_file.write_text("2 2026-08-12 08:03:27 1 0 15 0\n2 2026-08-12 08:05:12 1 0 15 0\n")
    records, errors = parse_dat_file(dat_file)
    assert len(records) == 2
    assert len(errors) == 0
    assert records[0].employee_id == "2"
    assert records[0].timestamp.strftime("%Y-%m-%d %H:%M:%S") == "2026-08-12 08:03:27"


def test_duplicate_timestamps_share_first_status() -> None:
    records = [
        _make_record("1001", "2026-08-12 08:00:00"),
        _make_record("1001", "2026-08-12 12:00:00"),
        _make_record("1001", "2026-08-12 12:00:00"),
        _make_record("1001", "2026-08-12 13:00:00"),
        _make_record("1001", "2026-08-12 13:00:00"),
        _make_record("1001", "2026-08-12 13:00:00"),
    ]
    processed = process_records(records)
    assert [r.status for r in processed] == [
        PunchStatus.IN,   # 08:00
        PunchStatus.OUT,  # 12:00
        PunchStatus.OUT,  # duplicate of 12:00
        PunchStatus.IN,   # 13:00
        PunchStatus.IN,   # duplicate of 13:00
        PunchStatus.IN,   # duplicate of 13:00
    ]


def test_duplicate_timestamps_count_as_one_for_unpaired() -> None:
    records = [
        _make_record("1001", "2026-08-12 08:00:00"),
        _make_record("1001", "2026-08-12 12:00:00"),
        _make_record("1001", "2026-08-12 12:00:00"),
        _make_record("1001", "2026-08-12 13:00:00"),
    ]
    processed = process_records(records)
    assert len(processed) == 4
    # 3 distinct timestamps: the final group is IN and unpaired
    for rec in processed:
        if rec.timestamp.strftime("%H:%M:%S") == "13:00:00":
            assert rec.status == PunchStatus.IN
            assert rec.exception_flag == "UNPAIRED_FINAL_IN"


def _group_by_employee(records):
    from collections import defaultdict
    groups = defaultdict(list)
    for record in records:
        groups[record.employee_id].append(record)
    return groups.items()
