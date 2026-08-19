"""Writer for the text-based `biotemplate.dat` fingerprint template index."""

from __future__ import annotations

from pathlib import Path

from lgus_dat.domain.biometric_template import BiometricTemplate


_FIELD_MAP = {
    "Pin": "pin",
    "No": "no",
    "Index": "index",
    "Valid": "valid",
    "Duress": "duress",
    "Type": "type",
    "MajorVer": "major_ver",
    "MinorVer": "minor_ver",
    "Format": "format",
    "Tmp": "tmp",
}


def write_biotemplate_dat(templates: list[BiometricTemplate], path: Path) -> None:
    """Write BiometricTemplate records to a tab-delimited `biotemplate.dat` file."""
    lines: list[str] = []
    for template in templates:
        fields = [f"{key}={getattr(template, attr)}" for key, attr in _FIELD_MAP.items()]
        lines.append("\t".join(fields))

    path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
