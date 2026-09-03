# Project Status

## MB10-VL Sequential IN/OUT `.DAT` Processor

### Current Version

`v0.32.1`

### Status

Added bulk department assignment to the PySide6 Employees page: users can select multiple employees (Ctrl/Shift-click) and assign them all to a department, or to no department, in a single action. The Employees table now displays the department as `ID - Name` (e.g. `1 - OFFICE OF THE MUNICIPAL MAYOR`) for readability instead of a raw department ID.

Improved Employees and Departments table column sizing: the ID columns now resize to their contents, while the remaining columns stretch. The department name column is prioritized with a larger initial share, so long department names are less likely to be truncated.

Pre-populated the SQLite registry with **19 municipal departments** and their department heads/positions from the submitted reference documents. The seed uses a `department_seed_version` marker so existing departments are overwritten once on the next app start, while future edits through the UI are preserved across restarts. **14 standard leave/status types** (Civil Service Form No. 6 leave types plus `Fieldwork`) are also pre-populated using the same versioned-seed approach, replacing the previous generic defaults.

Fixed DTR PDF `Remarks` cell text overflow: the column is wider, the font is smaller, and all remark cells are now `Paragraph` objects that wrap at word boundaries instead of squeezing or clipping long leave names such as `Special Privilege Leave` and `Special Leave Benefits for Women`.

Added an **Attendance Filing** page to the PySide6 desktop UI with three tabs: **Holidays** for system-wide holiday dates, **Leave Types** for a master status list, and **File Leave/Status** for per-employee date-range filings. The DTR PDF now looks up these holidays and filings when generating the monthly report and prints the status label(s) in the `Remarks` column; when both a holiday and an employee filing apply, the labels are combined. If no holiday or filing exists for a day, the column still shows the weekday abbreviation.

Added `head_position` to the `Department` model. The DTR PDF signature line now prints the department head name and position, replacing the generic `Verifying Officer` label. The PySide6 Employees page includes a `Head Position` field. The head name and position are stored in the local SQLite registry and do not affect the binary `department.dat` import/export.

The DTR PDF now calculates daily undertime for Monday-Friday workdays against the official 8:00 AM - 5:00 PM schedule. Late arrivals after 8:00 AM and early departures before 5:00 PM are counted in whole minutes and shown in the Undertime Hr/Min columns. Weekends are excluded, two-punch days use the final departure as the end time, and any day with a filed leave/status has zero undertime.

Added a `head_name` field to the `Department` model and registry. The DTR PDF "Verifying Officer" signature line is now derived from the employee's department head name. The PySide6 Employees page allows viewing and editing the department head name. The binary `department.dat` importer/exporter is unchanged because the device format does not carry head metadata; the value is stored in the local SQLite registry only.

Migrated the desktop UI from Tkinter to PySide6, with a new `desktop/` package providing a dashboard, import, processed records with date filters, reports, employees, and settings pages. Raw attendance logs are now persisted and loaded on startup, and month-scoped processing allows users to process only a selected month. A new **All Records** window loads every stored log directly from the registry, processes it on demand, and provides search and date filters so users always see accumulated data. The employee edit dialog in the PySide6 Employees page is now a modal Save dialog and uses a department dropdown and a position dropdown for assignment. The position dropdown is fed by a master Positions tab with full CRUD (add, rename, delete). The Employees tab top row has been converted from an inline add form into search filters for ID, name, full name, position, and department; adding an employee now opens a dedicated `Add Employee` dialog. The DTR PDF report now matches the reference government form with two side-by-side copies per page, a `DAILY TIME RECORD` title, AM/PM/Undertime/Remarks table, certification text, and signature block, and renders an employee's position below their name when set. Employee table refreshes now fully clear old rows before repopulating to prevent mixed/stale data when filtering, and numeric columns sort as numbers when clicking column headers. A Refresh button was also added to the Employees tab. The legacy Tkinter UI has been removed; shared application logic now lives in `src/lgus_dat/core/`. Build artifacts, stale `.spec` files, and unused imports were cleaned up; the GitHub Actions workflow now builds the PySide6 desktop app as `lgus-dat-desktop-V{VERSION}`. The `requirements.txt` and `pyproject.toml` dependencies now list only the packages required by the PySide6 desktop and CLI (`PySide6`, `reportlab`, `pytest`).

### Implemented

- [x] Project blueprint documented in `Docs/MB10-VL_Sequential_IN_OUT_Dev_Blueprint.md`
- [x] Agent instructions established in `AGENTS.md`
- [x] Core `.dat` parser (`src/lgus_dat/parser/dat_parser.py`)
- [x] Attendance sequence processor (`src/lgus_dat/processing/sequence_processor.py`)
- [x] CSV output writer (`src/lgus_dat/output/csv_writer.py`)
- [x] CLI entry point (`src/lgus_dat/cli/commands.py`)
- [x] Automated tests (`tests/test_*.py`)
- [x] Packaging configuration (`pyproject.toml`, `requirements.txt`)
- [x] PySide6 desktop UI (`src/lgus_dat/desktop/app.py`) with open/process/save workflow
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
- [x] Calendar date picker for date range filter (using PySide6 `QDateEdit`)
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
- [x] Modular PySide6 UI pages and widgets (`src/lgus_dat/desktop/pages/`, `src/lgus_dat/desktop/widgets/`)
- [x] Shared business logic controller (`src/lgus_dat/core/controller.py`)
- [x] Reusable date and search filters (`src/lgus_dat/core/date_filter.py`, `src/lgus_dat/core/search_filter.py`)
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
- [x] Employee `position` field shown below the name on DTR PDF reports
- [x] Master Positions tab with CRUD (add, rename, delete) in the PySide6 desktop UI
- [x] Employee position dropdown populated from the master positions list
- [x] Employees tab search filters by ID, name, full name, position, and department
- [x] Modal `Add Employee` dialog in the PySide6 desktop UI
- [x] Refresh button on the Employees tab
- [x] Numeric sorting for ID columns in Employees/Departments/Positions tables
- [x] Stale-row fix for filter/sort in the employee table
- [x] DTR PDF layout matching the reference government form with title, AM/PM/Undertime/Remarks, certification, signature, and two side-by-side copies per page
- [x] Pre-populated department defaults with heads and positions from reference documents
- [x] Pre-populated standard leave/status type defaults from Civil Service Form No. 6 plus `Fieldwork`
- [x] Versioned seeding for departments and leave types so defaults overwrite once but preserve future UI edits
- [x] DTR PDF `Remarks` cell word-wrap and font-size fix for long leave/status labels
- [x] Attendance Filing page with system-wide holidays, master leave/status types, and per-employee date-range filings
- [x] Dynamic DTR Remarks that print holiday and/or leave status labels instead of weekday abbreviations
- [x] Employee and department sorting by ID or name
- [x] Progress dialogs for imports, processing, and exports to keep UI responsive
- [x] PyInstaller build for the PySide6 desktop executable
- [x] Modal employee edit dialog in the PySide6 desktop UI
- [x] Department dropdown selection for employee assignment in PySide6
- [x] Bulk department assignment for multiple selected employees in PySide6
- [x] Department name display (`ID - Name`) in the Employees table

### In Progress

- [ ] End-to-end processing of real MB10-VL exports
- [ ] Duplicate detection and exception reporting

### Version History

|| Version | Date | Notes |
|| ------- | ---- | ----- |
|| v0.0.1 | 2026-08-12 | Initial blueprint and project scaffolding added. |
|| v0.1.0 | 2026-08-12 | Python package scaffold with parser, processor, CLI, and tests. |
|| v0.2.0 | 2026-08-12 | Desktop tkinter UI for open/process/save workflow. |
|| v0.3.0 | 2026-08-12 | `user.dat`/`department.dat` importers and SQLite employee registry. |
|| v0.4.0 | 2026-08-12 | Employee/department management editor and binary device-format exporters. |
|| v0.5.0 | 2026-08-12 | Date range selector to filter preview and processed output. |
|| v0.6.0 | 2026-08-12 | Processed `attlog.dat` exporter in NGteco/ZKTeco tab-delimited format. |
|| v0.7.0 | 2026-08-12 | PyInstaller/GitHub Actions build pipeline for Windows `.exe` and Linux binary. |
|| v0.8.0 | 2026-08-12 | Employee search filter for input preview and processed output by ID or name. |
|| v0.9.0 | 2026-08-12 | Manual IN/OUT status editing with `MANUAL_EDIT` flag for corrections. |
|| v0.10.0 | 2026-08-12 | Calendar date picker (`tkcalendar` DateEntry) for date range filter. |
|| v0.11.0 | 2026-08-12 | Local SQLite persistence of logs and `Process from DB` for centralized multi-device logs. |
|| v0.12.0 | 2026-08-12 | Search filter and clickable column sorting in employee/department management. |
|| v0.12.1 | 2026-08-12 | Processed `attlog.dat` export preserves the original Device ID padding/width from the source file. |
|| v0.12.2 | 2026-08-12 | Fixed `user.dat` binary export layout to match ZKTeco/NGteco ZK8 72-byte record format and prevent ID/name shifting. |
|| v0.12.3 | 2026-08-12 | Read the string User ID/PIN at byte 48 (not the single-byte UID) and default employee list/export to numeric sort. |
|| v0.12.4 | 2026-08-12 | Added a threaded progress bar for `user.dat`, `department.dat`, and `.DAT` imports so the UI stays responsive while files are parsed and stored. |
|| v0.13.0 | 2026-08-18 | Added full device backup import/export in Employee Management: `user.dat`, `department.dat`, `biotemplate.dat`, and raw `template.fp10*` files. |
|| v0.13.1 | 2026-08-19 | Hardcoded workcode to '1' in `attlog.dat` export for NGTeco software compatibility. Can be reverted if needed - see `src/lgus_dat/output/attlog_writer.py`. |
|| v0.14.0 | 2026-08-20 | Added time selection to date range filter for precise datetime filtering (HH:MM:SS format), color-coded status rows (IN=light blue, OUT=light yellow), and NGTeco-compatible `attlog.dat` export with workcode '1'. |
|| v0.15.0 | 2026-08-25 | Added DTR PDF generation with excel-like monthly attendance reports, duplicate punch handling, 4-punch time slot mapping, dynamic employee/department selection, and month picker for report generation. |
|| v0.16.0 | 2026-08-27 | Completed major UI refactoring to modular component architecture with separated concerns (components, views, dialogs, controller), reduced main app complexity by 38%, and improved maintainability for future UI framework migration. |
||| v0.17.0 | 2026-08-28 | Added initial PySide6 desktop scaffold and dependency. |
||| v0.18.0 | 2026-08-28 | Refactored UI to PySide6 with dashboard, import, processed, reports, employees, and settings pages; wired reports and employee management. |
||| v0.19.0 | 2026-08-28 | Added dashboard KPIs, theme styling, and PyInstaller packaging support. |
||| v0.20.0 | 2026-08-28 | Implemented month-scoped processing and polished PySide6 UI. |
||| v0.20.1 | 2026-08-28 | Fixed data persistence by loading stored attendance logs on startup and repaired Processed tab date range picker. |
||| v0.21.0 | 2026-08-28 | Added progress dialogs, employee full_name, manual status editing, DTR scope selection, and sorting. |
||| v0.22.0 | 2026-09-01 | Fixed imported attendance data accumulation and added an All Records window for viewing every stored, processed attendance record with search and date filters. |
||| v0.22.1 | 2026-09-01 | Added a performance benchmark and a progress dialog to the All Records window so loading and processing large registries does not freeze the UI. |
||| v0.23.0 | 2026-09-01 | Converted employee edit to a modal Save dialog and replaced the Department ID spin box with a department dropdown in the PySide6 UI. |
|||| v0.24.0 | 2026-09-02 | Reworked DTR PDF output to match the reference government form, with title, AM/PM/Undertime/Remarks table, certification, signature block, and two side-by-side copies per page. |
|| v0.25.0 | 2026-09-01 | Added master Positions tab with CRUD, employee position dropdown, and position rendered below the name on DTR PDF reports. |
|| v0.25.1 | 2026-09-01 | Converted the Employees tab top row into search filters and added a dedicated modal `Add Employee` dialog. |
|| v0.25.2 | 2026-09-02 | Fixed stale row mixing after filtering, numeric sorting for ID columns, and added a Refresh button to the Employees tab. |
||| v0.26.0 | 2026-09-02 | Added department `head_name` field, used it as the DTR PDF Verifying Officer, and exposed head-name editing in the PySide6 and Tkinter department management UIs. |
||| v0.27.0 | 2026-09-02 | Added DTR PDF undertime calculation for Mon-Fri 8:00 AM - 5:00 PM, counting late arrivals and early departures in Hr/Min columns. |
||| v0.28.0 | 2026-09-02 | Added department `head_position` field; DTR signature line now prints head name and position, replacing the generic `Verifying Officer` label. |
|||| v0.29.0 | 2026-09-02 | Added Attendance Filing page with holidays, leave/status types, and per-employee date-range filings; DTR Remarks now prints status labels and `Fieldwork` days have zero undertime. |
||| v0.30.0 | 2026-09-02 | Completed Tkinter-to-PySide6 migration: removed legacy `ui/`, moved shared controller/filters to `core/`, cleaned dead code and build artifacts, aligned CI build with `lgus-dat-desktop-V{VERSION}`, and updated project docs. |
||| v0.31.0 | 2026-09-02 | Pre-populated 19 municipal departments and 14 standard leave/status types using versioned seeds; fixed DTR PDF `Remarks` cell overflow for long leave labels by widening the column, reducing font size, and enabling word-wrap. |
||| v0.31.1 | 2026-09-02 | Updated DTR undertime relation to leave type logic so any filed leave/status type (not only `Fieldwork`) produces zero undertime; updated blueprint and DTR PDF docs accordingly. |
||| v0.32.0 | 2026-09-02 | Added bulk department assignment for multiple selected employees and department `ID - Name` display in the PySide6 Employees page. |

||| v0.32.1 | 2026-09-03 | Improved Employees and Departments table column sizing so long department names are more visible. |

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
