"""Department domain model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Department:
    """Department record derived from a device `department.dat` export."""

    department_id: int
    name: str
