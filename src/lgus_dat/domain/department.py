"""Department domain model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class Department:
    """Department record derived from a device `department.dat` export."""

    department_id: int
    name: str
    raw_record: Optional[bytes] = None
    head_name: Optional[str] = None
