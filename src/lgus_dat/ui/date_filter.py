"""Date-range helpers for filtering records in the UI."""

from __future__ import annotations

from datetime import date
from typing import Callable, Optional, TypeVar

T = TypeVar("T")


def in_date_range(record_date: date, start: Optional[date], end: Optional[date]) -> bool:
    """Return True if *record_date* falls within the inclusive [start, end] range."""
    if start is not None and record_date < start:
        return False
    if end is not None and record_date > end:
        return False
    return True


def filter_by_date(
    records: list[T],
    date_accessor: Callable[[T], date],
    start: Optional[date] = None,
    end: Optional[date] = None,
) -> list[T]:
    """Return the subset of *records* whose date is within the inclusive range."""
    return [rec for rec in records if in_date_range(date_accessor(rec), start, end)]
