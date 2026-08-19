"""Tests for biotemplate.dat writer."""

from pathlib import Path

from lgus_dat.domain.biometric_template import BiometricTemplate
from lgus_dat.exporters.biotemplate_writer import write_biotemplate_dat
from lgus_dat.importers.biotemplate_parser import parse_biotemplate_dat


def test_write_biotemplate_dat_round_trip(tmp_path: Path) -> None:
    templates = [
        BiometricTemplate(
            pin="1",
            no=0,
            index=0,
            valid=1,
            duress=0,
            type=9,
            major_ver=35,
            minor_ver=4,
            format=0,
            tmp="abc123",
        ),
        BiometricTemplate(
            pin="2",
            no=0,
            index=0,
            valid=1,
            duress=0,
            type=9,
            major_ver=35,
            minor_ver=4,
            format=0,
            tmp="def456",
        ),
    ]

    path = tmp_path / "biotemplate.dat"
    write_biotemplate_dat(templates, path)

    parsed = parse_biotemplate_dat(path)
    assert parsed == templates
