# Project Status

## MB10-VL Sequential IN/OUT `.DAT` Processor

### Current Version

`v0.22.0`

### Status

Migrated the desktop UI from Tkinter to PySide6, with a new `desktop/` package providing a dashboard, import, processed records with date filters, reports, employees, and settings pages. Raw attendance logs are now persisted and loaded on startup, and month-scoped processing allows users to process only a selected month. A new **All Records** window loads every stored log directly from the registry, processes it on demand, and provides search and date filters so users always see accumulated data. The legacy Tkinter UI remains in `ui/`.

### Implemented

- [x] Project blueprint documented in `Docs/MB10-VL_Sequential_IN_OUT_Dev_Blueprint.md`
- [x] Agent instructions established in `AGENTS.md`
- [x] Core `.dat` parser (`src/lgus_dat/parser/dat_parser.py`)
- [x] Attendance sequence processor (`src/lgus_dat/processing/sequence_processor.py`)
- [x] CSV output writer (`src/lgus_dat/output/csv_writer.py`)
- [x] CLI entry point (`src/lgus_dat/cli/commands.py`)
- [x] Automated tests (`tests/test_*.py`)
- [x] Packaging configuration (`pyproject.toml`, `requirements.txt`)
- [x] Desktop tkinter UI (`src/lgus_dat/ui/app.py`) with open/process/save workflow
- [x] `user.dat` employee master importer (`src/lgus_dat/importers/user_parser.py`)
- [x] `department.dat` importer (`src/lgus_dat/importers/department_parser.py`)
- [x] SQLite employee/department registry (`src/lgus_dat/persistence/registry.py`)
- [x] UI/CSV name resolution from registry
- [x] Employee/department management editor and binary `user.dat`/`department.dat` exporters
- [x] Date range filter for input preview and processed output
- [x] Processed `attlog.dat` exporter and UI button
- [x] Standalone executable build pipeline (PyInstaller + GitHub Actions)
- [x] Employee search filter for input preview and processed output by ID or name
- [x] Manual IN/OUT status editing with `MANUAL_EDIT` flag for corrections
- [x] Calendar date picker for date range filter (using `tkcalendar` DateEntry)
- [x] Time selection in date range filter for precise datetime filtering (HH:MM:SS format)
- [x] Color-coded status rows in output tree (IN=light blue, OUT=light yellow)
- [x] Local SQLite persistence of imported attendance logs with multi-device/source support
- [x] `Process from DB` to process all centralized stored logs
- [x] Search filter and column sorting in the employee/department management window
- [x] NGTeco-compatible `attlog.dat` export with workcode '1'
- [x] DTR PDF generation with excel-like monthly attendance reports (`src/lgus_dat/output/pdf_writer.py`)
- [x] Duplicate punch handling (keeps first occurrence of same timestamp)
- [x] 4-punch mapping to time slots (IN AM, OUT AM, IN PM, OUT PM)
- [x] Month picker for DTR report generation in GUI
- [x] Dynamic employee/department selection dialog for PDF reports
- [x] ReportLab integration for PDF generation
- [x] Modular UI component architecture (`src/lgus_dat/ui/components/`)
- [x] Separated UI views for data display (`src/lgus_dat/ui/views/`)
- [x] Isolated modal dialogs (`src/lgus_dat/ui/dialogs/`)
- [x] Business logic controller (`src/lgus_dat/ui/controller.py`)
- [x] Reduced main app complexity from ~750 to ~465 lines
- [x] Component-based UI for improved maintainability and testability
- [x] PySide6 desktop application (`src/lgus_dat/desktop/app.py`) with sidebar navigation and stacked pages
- [x] Dashboard page with real-time KPI cards and quick actions
- [x] Import page with raw input preview and month-scoped processing
- [x] Processed page with employee search and date range filter
- [x] Reports page for DTR PDF, CSV, and attlog export
- [x] Employees and departments management page
- [x] Light and dark theme support for PySide6 UI
- [x] Standalone **All Records** window with search and date filters for viewing all accumulated, processed attendance records
- [x] Attendance log persistence and automatic reload on startup
- [x] Manual IN/OUT status editing with `MANUAL_EDIT` flag in the PySide6 UI
- [x] DTR PDF scope selection by all employees, department, or specific employees
- [x] Employee `full_name` field for DTR PDF output
- [x] Employee and department sorting by ID or name
- [x] Progress dialogs for imports, processing, and exports to keep UI responsive
- [x] PyInstaller build for the PySide6 desktop executable

### In Progress

- [ ] End-to-end processing of real MB10-VL exports
- [ ] Duplicate detection and exception reporting

### Version History

| Version | Date | Notes |
| ------- | ---- | ----- |
| v0.0.1 | 2026-08-12 | Initial blueprint and project scaffolding added. |
| v0.1.0 | 2026-08-12 | Python package scaffold with parser, processor, CLI, and tests. |
| v0.2.0 | 2026-08-12 | Desktop tkinter UI for open/process/save workflow. |
| v0.3.0 | 2026-08-12 | `user.dat`/`department.dat` importers and SQLite employee registry. |
| v0.4.0 | 2026-08-12 | Employee/department management editor and binary device-format exporters. |
| v0.5.0 | 2026-08-12 | Date range selector to filter preview and processed output. |
| v0.6.0 | 2026-08-12 | Processed `attlog.dat` exporter in NGteco/ZKTeco tab-delimited format. |
| v0.7.0 | 2026-08-12 | PyInstaller/GitHub Actions build pipeline for Windows `.exe` and Linux binary. |
| v0.8.0 | 2026-08-12 | Employee search filter for input preview and processed output by ID or name. |
| v0.9.0 | 2026-08-12 | Manual IN/OUT status editing with `MANUAL_EDIT` flag for corrections. |
| v0.10.0 | 2026-08-12 | Calendar date picker (`tkcalendar` DateEntry) for date range filter. |
| v0.11.0 | 2026-08-12 | Local SQLite persistence of imported logs and `Process from DB` for centralized multi-device logs. |
| v0.12.0 | 2026-08-12 | Search filter and clickable column sorting in employee/department management. |
| v0.12.1 | 2026-08-12 | Processed `attlog.dat` export preserves the original Device ID padding/width from the source file. |
| v0.12.2 | 2026-08-12 | Fixed `user.dat` binary export layout to match ZKTeco/NGteco ZK8 72-byte record format and prevent ID/name shifting. |
| v0.12.3 | 2026-08-12 | Read the string User ID/PIN at byte 48 (not the single-byte UID) and default employee list/export to numeric sort. |
| v0.12.4 | 2026-08-12 | Added a threaded progress bar for `user.dat`, `department.dat`, and `.DAT` imports so the UI stays responsive while files are parsed and stored. |
| v0.13.0 | 2026-08-18 | Added full device backup import/export in Employee Management: `user.dat`, `department.dat`, `biotemplate.dat`, and raw `template.fp10*` files. |
| v0.13.1 | 2026-08-19 | Hardcoded workcode to '1' in `attlog.dat` export for NGTeco software compatibility. Can be reverted if needed - see `src/lgus_dat/output/attlog_writer.py`. |
| v0.14.0 | 2026-08-20 | Added time selection to date range filter for precise datetime filtering (HH:MM:SS format), color-coded status rows (IN=light blue, OUT=light yellow), and NGTeco-compatible `attlog.dat` export with workcode '1'. |
| v0.15.0 | 2026-08-25 | Added DTR PDF generation with excel-like monthly attendance reports, duplicate punch handling, 4-punch time slot mapping, dynamic employee/department selection, and month picker for report generation. |
| v0.16.0 | 2026-08-27 | Completed major UI refactoring to modular component architecture with separated concerns (components, views, dialogs, controller), reduced main app complexity by 38%, and improved maintainability for future UI framework migration. |
|| v0.17.0 | 2026-08-28 | Added initial PySide6 desktop scaffold and dependency. |
|| v0.18.0 | 2026-08-28 | Refactored UI to PySide6 with dashboard, import, processed, reports, employees, and settings pages; wired reports and employee management. |
|| v0.19.0 | 2026-08-28 | Added dashboard KPIs, theme styling, and PyInstaller packaging support. |
|| v0.20.0 | 2026-08-28 | Implemented month-scoped processing and polished PySide6 UI. |
|| v0.20.1 | 2026-08-28 | Fixed data persistence by loading stored attendance logs on startup and repaired Processed tab date range picker. |
|| v0.21.0 | 2026-08-28 | Added progress dialogs, employee full_name, manual status editing, DTR scope selection, and sorting. |
|| v0.22.0 | 2026-09-01 | Fixed imported attendance data accumulation and added an All Records window for viewing every stored, processed attendance record with search and date filters. |

Bump the version in this file whenever a significant milestone, feature, or release is completed.

## Distribution and Installation Plan

To make LGUS-DAT easier to run for HR staff, consider the following distribution formats:

1. **One-file executable (current)**: `lgus-dat-desktop-V{VERSION}.exe` — single file, but slow startup and may trigger antivirus scanners.
2. **Portable ZIP**: Build as a one-directory PyInstaller bundle, zip `dist/desktop/lgus-dat-desktop-V{VERSION}`, and distribute. Users unzip and run `lgus-dat-desktop-V{VERSION}.exe`.
3. **Windows installer**: Use Inno Setup or a WiX/MSI project to create `LGUS-DAT-Setup-V{VERSION}.exe` that installs to `%ProgramFiles%`, creates Start Menu shortcuts, and registers an uninstall entry.
4. **MSIX package**: For Microsoft Store submission or enterprise sideloading.
5. **Size reduction**: For the PySide6 build, exclude unused heavy modules such as `tkinter` and `_tkinter`, enable UPX compression, and prefer one-directory builds to avoid one-file extraction overhead.
6. **User-writable data directory**: When installed under `%ProgramFiles%`, store `lgus_registry.db` and settings under `%APPDATA%/LGUS-DAT` so the app works without admin rights.

Recommended near-term: keep the one-file build for quick testing and add a one-directory **portable ZIP** plus an **Inno Setup installer** for end users.
