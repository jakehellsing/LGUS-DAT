"""Substring search helpers for the desktop UI record lists."""

from __future__ import annotations

from typing import Callable, Optional, TypeVar

T = TypeVar("T")


def matches_search(query: str, *values: Optional[str]) -> bool:
    """Return True when the trimmed query matches any of the values (case-insensitive)."""
    q = query.strip().lower()
    if not q:
        return True
    for value in values:
        if value is not None and q in value.lower():
            return True
    return False


def filter_by_search(
    records: list[T],
    query: str,
    accessors: list[Callable[[T], Optional[str]]],
) -> list[T]:
    """Filter records by substring match across the supplied string accessors."""
    q = query.strip().lower()
    if not q:
        return records

    def match(record: T) -> bool:
        return any(q in ((value or "").lower()) for value in (accessor(record) for accessor in accessors))

    return [rec for rec in records if match(rec)]
