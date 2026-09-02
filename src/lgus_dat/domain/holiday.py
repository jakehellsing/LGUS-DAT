"""Holiday domain model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class Holiday:
    """A system-wide holiday that affects every employee's DTR remarks."""

    holiday_date: date
    name: str
