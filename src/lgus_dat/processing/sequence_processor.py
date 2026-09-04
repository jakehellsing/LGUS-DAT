"""Core business logic: assign IN/OUT by chronological punch sequence."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from typing import Callable, Iterable, Optional

from lgus_dat.domain.attendance_record import AttendanceRecord, PunchStatus
from lgus_dat.parser.dat_parser import ParsedRecord


def group_records(records: Iterable[ParsedRecord]) -> dict[tuple[str, date], list[ParsedRecord]]:
    """Group parsed records by employee_id and calendar date."""
    groups: dict[tuple[str, date], list[ParsedRecord]] = defaultdict(list)
    for record in records:
        key = (record.employee_id, record.timestamp.date())
        groups[key].append(record)
    return groups


def sort_group(group: list[ParsedRecord]) -> list[ParsedRecord]:
    """Sort records by timestamp, preserving source order for identical timestamps."""
    return sorted(group, key=lambda r: (r.timestamp, r.fields))


def assign_status(index: int) -> PunchStatus:
    """Even index -> IN, odd index -> OUT."""
    return PunchStatus.IN if index % 2 == 0 else PunchStatus.OUT


NameLookup = Optional[Callable[[str], Optional[str]]]


def process_records(
    records: Iterable[ParsedRecord],
    name_lookup: NameLookup = None,
) -> list[AttendanceRecord]:
    """Assign IN/OUT statuses per employee and calendar date.

    Groups by employee + date, sorts chronologically, then alternates starting
    with IN. Odd-length groups are flagged UNPAIRED_FINAL_IN.
    """
    results: list[AttendanceRecord] = []
    groups = group_records(records)

    for key in sorted(groups):
        employee_id, punch_date = key
        sorted_records = sort_group(groups[key])

        # Consecutive records with the exact same timestamp are treated as one
        # punch event for IN/OUT status assignment.
        blocks: list[list[ParsedRecord]] = []
        for raw in sorted_records:
            if blocks and raw.timestamp == blocks[-1][0].timestamp:
                blocks[-1].append(raw)
            else:
                blocks.append([raw])

        unpaired = len(blocks) % 2 == 1

        for block_index, block in enumerate(blocks):
            status = assign_status(block_index)
            exception: Optional[str] = None
            if unpaired and block_index == len(blocks) - 1 and status == PunchStatus.IN:
                exception = "UNPAIRED_FINAL_IN"

            for raw in block:
                results.append(
                    AttendanceRecord(
                        employee_id=employee_id,
                        punch_date=punch_date,
                        punch_time=raw.timestamp.strftime("%H:%M:%S"),
                        timestamp=raw.timestamp,
                        status=status,
                        original_record=raw.original_line,
                        exception_flag=exception,
                        employee_name=name_lookup(employee_id) if name_lookup else None,
                    )
                )

    return results
