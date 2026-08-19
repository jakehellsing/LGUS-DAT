"""Tests for biometric template and raw file storage in the registry."""

from pathlib import Path

from lgus_dat.domain.biometric_template import BiometricTemplate
from lgus_dat.persistence.registry import AttendanceRegistry


def _sample_template(pin: str = "1") -> BiometricTemplate:
    return BiometricTemplate(
        pin=pin,
        no=0,
        index=0,
        valid=1,
        duress=0,
        type=9,
        major_ver=35,
        minor_ver=4,
        format=0,
        tmp="abc123",
    )


def test_import_and_retrieve_biotemplates(tmp_path: Path) -> None:
    db = tmp_path / "registry.db"
    reg = AttendanceRegistry(db_path=db)

    t1 = _sample_template("1")
    t2 = _sample_template("2")
    t2_no1 = BiometricTemplate(pin="2", no=1, index=0, valid=1, duress=0, type=9, major_ver=35, minor_ver=4, format=0, tmp="xyz")

    assert reg.import_biotemplates([t1, t2, t2_no1]) == 3
    assert reg.all_biotemplates() == [t1, t2, t2_no1]
    assert reg.biotemplates_for_pin("2") == [t2, t2_no1]


def test_update_and_delete_biotemplate_pin(tmp_path: Path) -> None:
    db = tmp_path / "registry.db"
    reg = AttendanceRegistry(db_path=db)

    reg.import_biotemplates([_sample_template("1")])
    reg.update_biotemplate_pin("1", "10")
    assert reg.biotemplates_for_pin("10") == [_sample_template("10")]
    assert reg.biotemplates_for_pin("1") == []

    reg.delete_biotemplates_for_pin("10")
    assert reg.all_biotemplates() == []


def test_import_and_export_template_files(tmp_path: Path) -> None:
    db = tmp_path / "registry.db"
    reg = AttendanceRegistry(db_path=db)

    files = {"template.fp10": b"raw1", "template.fp10.1": b"raw2"}
    assert reg.import_template_files(files) == 2
    assert reg.all_template_files() == files
