# LGUS-DAT

MB10-VL Sequential IN/OUT `.DAT` Processor.

This project consumes raw `.dat` attendance exports from a ZKTeco MB10-VL biometric terminal and assigns `IN`/`OUT` status by chronological punch sequence.

## Core Rule

> For each employee and calendar date, sort raw punches chronologically and alternate `IN`/`OUT` starting with `IN`.

See `Docs/MB10-VL_Sequential_IN_OUT_Dev_Blueprint.md` for full requirements and `Docs/DTR_PDF_Generation.md` for PDF report documentation.

## Project Structure

```
src/
  lgus_dat/
    parser/         .DAT parsing
    importers/      Device master file importers
    persistence/    SQLite employee/department registry
    domain/         Attendance models
    processing/     Sequence logic
    output/         CSV and PDF writers
    cli/            Command-line entry point
    ui/             Desktop tkinter interface

tests/              Automated tests
Docs/               Blueprint, status, and feature guides
```

## Usage

Install in editable mode:

```bash
pip install -e .
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Process a `.dat` file:

```bash
python -m lgus_dat.cli.commands sample.dat
# or
lgus-dat sample.dat --output-dir output --archive-dir archive
```

Launch the desktop UI:

```bash
python -m lgus_dat.ui.app
# or
lgus-dat-gui
```

The UI lets you open a `.dat` file, preview the raw records, process them into IN/OUT rows, and save the resulting CSV.

**Features:**
- Date and time range filtering for precise datetime selection (HH:MM:SS format)
- Color-coded status rows (IN=light blue, OUT=light yellow)
- NGTeco-compatible `attlog.dat` export with workcode '1'
- Employee search filter by ID or name
- Manual IN/OUT status editing with correction flags
- **DTR PDF generation** with excel-like monthly attendance reports
- Duplicate punch handling (keeps first occurrence of same timestamp)
- 4-punch mapping to time slots (IN AM, OUT AM, IN PM, OUT PM)
- Dynamic employee/department selection for reports

You can also import the device's `user.dat` to resolve employee names from numeric IDs and `department.dat` to build a department registry. Use **Manage Employees** to view, add, edit, or delete employees and departments, then export them back to the same ZKTeco/NGteco binary `user.dat` / `department.dat` formats for re-import into the device.

## Standalone Executable

Pre-built Windows and Linux executables are produced by GitHub Actions for every push to `main`. Download the artifact for your platform from the **Build Executables** workflow run, then run `LGUS-DAT.exe` (Windows) or `LGUS-DAT` (Linux) directly — no Python installation is needed on the target PC.

To build locally with PyInstaller:

```bash
pip install -e ".[build]"
pyinstaller --onefile --windowed --name LGUS-DAT scripts/gui_entry.py
```

The output will be in `dist/LGUS-DAT` (Linux) or `dist/LGUS-DAT.exe` (Windows).
