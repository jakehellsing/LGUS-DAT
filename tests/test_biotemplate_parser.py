"""Tests for biotemplate.dat parser."""

from pathlib import Path

from lgus_dat.domain.biometric_template import BiometricTemplate
from lgus_dat.importers.biotemplate_parser import parse_biotemplate_dat


def test_parse_biotemplate_dat(tmp_path: Path) -> None:
    path = tmp_path / "biotemplate.dat"
    line = "Pin=2\tNo=0\tIndex=0\tValid=1\tDuress=0\tType=9\tMajorVer=35\tMinorVer=4\tFormat=0\tTmp=SGVsbG8="
    path.write_text(line + "\r\n", encoding="utf-8")

    templates = parse_biotemplate_dat(path)
    assert len(templates) == 1
    t = templates[0]
    assert t == BiometricTemplate(
        pin="2",
        no=0,
        index=0,
        valid=1,
        duress=0,
        type=9,
        major_ver=35,
        minor_ver=4,
        format=0,
        tmp="SGVsbG8=",
    )


def test_parse_biotemplate_dat_skips_invalid_lines(tmp_path: Path) -> None:
    path = tmp_path / "biotemplate.dat"
    path.write_text("\nPin=1\tTmp=abc\nno equal signs\n", encoding="utf-8")
    templates = parse_biotemplate_dat(path)
    assert len(templates) == 1
    assert templates[0].pin == "1"
