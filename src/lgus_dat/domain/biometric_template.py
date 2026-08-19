"""Biometric template domain model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BiometricTemplate:
    """Fingerprint/face template record derived from a device `biotemplate.dat` export."""

    pin: str
    no: int
    index: int
    valid: int
    duress: int
    type: int
    major_ver: int
    minor_ver: int
    format: int
    tmp: str
