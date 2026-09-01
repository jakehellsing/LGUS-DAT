"""Performance benchmark for attendance loading and processing operations."""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from pathlib import Path

from lgus_dat.output.pdf_writer import generate_dtr_pdf, group_records_by_employee
from lgus_dat.parser.dat_parser import parse_dat_file
from lgus_dat.persistence.registry import AttendanceRegistry
from lgus_dat.processing.sequence_processor import process_records


RECORD_COUNT = 10000
TEMP_DIR = Path("C:/temp")


def _ensure_temp_dir() -> None:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def _make_dat_file(path: Path, records: int) -> None:
    base = datetime(2026, 8, 1, 7, 0, 0)
    with path.open("w", encoding="utf-8") as f:
        for i in range(records):
            ts = base + timedelta(seconds=i * 5)
            f.write(f"2 {ts:%Y-%m-%d %H:%M:%S} 1 0 15 0\n")


def test_parse_performance() -> float:
    _ensure_temp_dir()
    dat_file = TEMP_DIR / "perf_attendance.dat"
    _make_dat_file(dat_file, RECORD_COUNT)

    t0 = time.perf_counter()
    records, _ = parse_dat_file(dat_file)
    t1 = time.perf_counter()
    elapsed = t1 - t0
    print(f"parse_dat_file ({len(records)} records): {elapsed:.3f}s")
    return elapsed


def test_import_performance() -> float:
    _ensure_temp_dir()
    dat_file = TEMP_DIR / "perf_attendance.dat"
    db_file = TEMP_DIR / "perf_import.db"
    db_file.unlink(missing_ok=True)
    _make_dat_file(dat_file, RECORD_COUNT)

    records, _ = parse_dat_file(dat_file)
    registry = AttendanceRegistry(db_path=db_file)

    t0 = time.perf_counter()
    count = registry.import_attendance_logs(records, dat_file)
    t1 = time.perf_counter()
    elapsed = t1 - t0
    print(f"import_attendance_logs ({count} new records): {elapsed:.3f}s")
    return elapsed


def test_load_and_process_performance() -> float:
    _ensure_temp_dir()
    dat_file = TEMP_DIR / "perf_attendance.dat"
    db_file = TEMP_DIR / "perf_load.db"
    db_file.unlink(missing_ok=True)
    _make_dat_file(dat_file, RECORD_COUNT)

    records, _ = parse_dat_file(dat_file)
    registry = AttendanceRegistry(db_path=db_file)
    registry.import_attendance_logs(records, dat_file)

    t0 = time.perf_counter()
    logs = registry.get_attendance_logs()
    employees = {emp.device_user_id: emp.name for emp in registry.all_employees()}
    processed = process_records(logs, name_lookup=employees.get)
    t1 = time.perf_counter()
    elapsed = t1 - t0
    print(f"get_attendance_logs + process_records ({len(processed)} processed): {elapsed:.3f}s")
    return elapsed


def test_pdf_generation_performance() -> float:
    _ensure_temp_dir()
    dat_file = TEMP_DIR / "perf_attendance.dat"
    db_file = TEMP_DIR / "perf_pdf.db"
    db_file.unlink(missing_ok=True)
    _make_dat_file(dat_file, RECORD_COUNT)

    records, _ = parse_dat_file(dat_file)
    registry = AttendanceRegistry(db_path=db_file)
    registry.import_attendance_logs(records, dat_file)

    logs = registry.get_attendance_logs()
    employees = {emp.device_user_id: emp.name for emp in registry.all_employees()}
    processed = process_records(logs, name_lookup=employees.get)
    grouped = group_records_by_employee(processed)
    pdf_path = TEMP_DIR / "perf_dtr.pdf"
    pdf_path.unlink(missing_ok=True)

    t0 = time.perf_counter()
    generate_dtr_pdf(
        employee_records=grouped,
        month=date(2026, 8, 1),
        output_path=pdf_path,
        employee_names=employees,
    )
    t1 = time.perf_counter()
    elapsed = t1 - t0
    print(f"generate_dtr_pdf ({len(grouped)} employees): {elapsed:.3f}s")
    return elapsed


def main() -> None:
    print("LGUS-DAT performance benchmark")
    print(f"Dataset: {RECORD_COUNT} attendance records for one employee across one month")
    print("-" * 60)
    test_parse_performance()
    test_import_performance()
    test_load_and_process_performance()
    test_pdf_generation_performance()
    print("-" * 60)
    print("Done")


if __name__ == "__main__":
    main()
