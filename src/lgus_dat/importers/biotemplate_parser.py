"""Parser for the text-based `biotemplate.dat` fingerprint template index."""

from __future__ import annotations

import re
from pathlib import Path

from lgus_dat.domain.biometric_template import BiometricTemplate


_FIELD_ORDER = (
    "Pin",
    "No",
    "Index",
    "Valid",
    "Duress",
    "Type",
    "MajorVer",
    "MinorVer",
    "Format",
    "Tmp",
)

_INT_FIELDS = {"No", "Index", "Valid", "Duress", "Type", "MajorVer", "MinorVer", "Format"}


def parse_biotemplate_dat(path: Path) -> list[BiometricTemplate]:
    """Parse a tab-delimited `biotemplate.dat` file into BiometricTemplate records."""
    templates: list[BiometricTemplate] = []
    text = path.read_text(encoding="utf-8", errors="replace")

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        parsed: dict[str, str] = {}
        for match in re.finditer(r"(\w+)=([^\t]+)", line):
            parsed[match.group(1)] = match.group(2).strip()

        if "Pin" not in parsed or "Tmp" not in parsed:
            continue

        def _int(key: str, default: int = 0) -> int:
            try:
                return int(parsed.get(key, default))
            except ValueError:
                return default

        templates.append(
            BiometricTemplate(
                pin=parsed["Pin"],
                no=_int("No"),
                index=_int("Index"),
                valid=_int("Valid", 1),
                duress=_int("Duress"),
                type=_int("Type"),
                major_ver=_int("MajorVer"),
                minor_ver=_int("MinorVer"),
                format=_int("Format"),
                tmp=parsed["Tmp"],
            )
        )

    return templates
