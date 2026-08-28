# LGUS-DAT

MB10-VL Sequential IN/OUT `.DAT` Processor.

This project consumes raw `.dat` attendance exports from a ZKTeco MB10-VL biometric terminal and assigns `IN`/`OUT` status by chronological punch sequence.

## Core Rule

> For each employee and calendar date, sort raw punches chronologically and alternate `IN`/`OUT` starting with `IN`.

See `Docs/MB10-VL_Sequential_IN_OUT_Dev_Blueprint.md` for full requirements, `Docs/DTR_PDF_Generation.md` for PDF report documentation, and `Docs/UI_Architecture.md` for UI component architecture details.

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
    ui/             Legacy Tkinter desktop interface (modular components)
      components/   Reusable UI components (toolbars, panels, dialogs)
      views/        Data display components (treeviews, status panels)
      dialogs/      Modal dialogs (management, selection, editing)
      controller.py Business logic coordination
      app.py        Main application orchestration
    desktop/        New PySide6 desktop interface
      pages/        Page views (dashboard, import, processed, reports, employees, settings)
      widgets/      Reusable widgets (kpi_card, data_table)
      desktop_controller.py  Adapter for UIController
      main_window.py         Main window with sidebar navigation
      app.py                 PySide6 entry point
      theme.py               Light/dark theme definitions

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

Launch the new PySide6 desktop UI:

```bash
python -m lgus_dat.desktop.app
# or
lgus-dat-desktop
```

The legacy Tkinter UI is still available:

```bash
python -m lgus_dat.ui.app
# or
lgus-dat-gui
```

The PySide6 desktop UI lets you import `.dat` files, process them into IN/OUT rows, view processed records with date and search filters, generate DTR PDFs, export CSV and attlog files, and manage employees and departments.

**PySide6 Desktop Features:**
- Sidebar navigation with Dashboard, Import, Processed, Reports, Employees, and Settings
- Light and dark themes
- Dashboard KPI cards (total employees, imported logs, processed records, unpaired IN)
- Month-scoped processing to avoid reprocessing all stored data
- Date and time range filtering for precise datetime selection
- Employee search filter by ID or name
- **DTR PDF generation** with excel-like monthly attendance reports
- DTR report scope selection (all, by department, by specific employees)
- CSV and NGTeco-compatible `attlog.dat` export with workcode '1'
- Employee and department management with CRUD operations
- Employee full-name profile for DTR PDF output only
- Employee and department sorting by ID or name
- Manual IN/OUT status editing with `MANUAL_EDIT` flag
- Progress dialogs for imports, processing, and exports to keep UI responsive
- Data persistence: raw logs are stored in SQLite and loaded on startup

**Legacy Tkinter Features:**
- Color-coded status rows (IN=light blue, OUT=light yellow)
- Manual IN/OUT status editing with correction flags
- Duplicate punch handling (keeps first occurrence of same timestamp)
- 4-punch mapping to time slots (IN AM, OUT AM, IN PM, OUT PM)
- Dynamic employee/department selection for reports
- **Modular UI architecture** for easy maintenance and future framework migration

You can also import the device's `user.dat` to resolve employee names from numeric IDs and `department.dat` to build a department registry. Use **Manage Employees** to view, add, edit, or delete employees and departments, then export them back to the same ZKTeco/NGteco binary `user.dat` / `department.dat` formats for re-import into the device.

**Department Management Features:**
- Dropdown department selection for employee assignment (shows department names instead of IDs)
- Department details view with employee count and member management
- Add/remove employees from departments with visual interface
- Safety checks to prevent deletion of departments with assigned employees
- Real-time employee count updates per department

## Standalone Executable

Pre-built Windows and Linux executables are produced by GitHub Actions for every push to `main`. Download the artifact for your platform from the **Build Executables** workflow run, then run `LGUS-DAT.exe` (Windows) or `LGUS-DAT` (Linux) directly — no Python installation is needed on the target PC.

To build the PySide6 desktop app locally with PyInstaller:

```bash
pip install -e ".[build]"
pyinstaller --onefile --windowed --name lgus-dat-desktop --distpath dist/desktop --workpath build/desktop --noconfirm src/lgus_dat/desktop/app.py
```

The output will be in `dist/desktop/lgus-dat-desktop.exe` (Windows) or `dist/desktop/lgus-dat-desktop` (Linux).
