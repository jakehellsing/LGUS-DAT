"""Date-range helpers for filtering records in the UI."""

from __future__ import annotations

from datetime import date, datetime
from typing import Callable, Optional, TypeVar, Union

T = TypeVar("T")
DateOrDatetime = Union[date, datetime]


def in_date_range(record_date: DateOrDatetime, start: Optional[DateOrDatetime], end: Optional[DateOrDatetime]) -> bool:
    """Return True if *record_date* falls within the inclusive [start, end] range."""
    if start is not None and record_date < start:
        return False
    if end is not None and record_date > end:
        return False
    return True


def filter_by_date(
    records: list[T],
    date_accessor: Callable[[T], DateOrDatetime],
    start: Optional[DateOrDatetime] = None,
    end: Optional[DateOrDatetime] = None,
) -> list[T]:
    """Return the subset of *records* whose date is within the inclusive range."""
    return [rec for rec in records if in_date_range(date_accessor(rec), start, end)]
