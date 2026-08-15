"""Tests for UI date-range filter helpers."""

from datetime import date

from lgus_dat.ui.date_filter import filter_by_date, in_date_range


def _make_record(employee_id: str, record_date: date) -> dict:
    return {"employee_id": employee_id, "date": record_date}


def test_in_date_range() -> None:
    assert in_date_range(date(2026, 8, 12), None, None) is True
    assert in_date_range(date(2026, 8, 12), date(2026, 8, 10), date(2026, 8, 15)) is True
    assert in_date_range(date(2026, 8, 9), date(2026, 8, 10), date(2026, 8, 15)) is False
    assert in_date_range(date(2026, 8, 16), date(2026, 8, 10), date(2026, 8, 15)) is False


def test_filter_by_date() -> None:
    records = [
        _make_record("1", date(2026, 8, 10)),
        _make_record("2", date(2026, 8, 12)),
        _make_record("3", date(2026, 8, 15)),
    ]
    filtered = filter_by_date(records, lambda r: r["date"], date(2026, 8, 11), date(2026, 8, 13))
    assert [r["employee_id"] for r in filtered] == ["2"]
