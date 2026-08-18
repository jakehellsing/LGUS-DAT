"""Employee domain model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class Employee:
    """Employee record derived from a device `user.dat` export."""

    device_user_id: str
    name: str
    department_id: Optional[int] = None
    raw_record: Optional[bytes] = None
    uid: Optional[int] = None
    privilege: Optional[int] = None
    password: Optional[str] = None
    group_id: Optional[str] = None
    card: Optional[int] = None
