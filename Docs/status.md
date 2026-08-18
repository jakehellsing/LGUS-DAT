# Project Status

## MB10-VL Sequential IN/OUT `.DAT` Processor

### Current Version

`v0.12.0`

### Status

The Manage Employees window now has a search filter and clickable column sorting to quickly find and organize employees.

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
- [x] Local SQLite persistence of imported attendance logs with multi-device/source support
- [x] `Process from DB` to process all centralized stored logs
- [x] Search filter and column sorting in the employee/department management window

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

Bump the version in this file whenever a significant milestone, feature, or release is completed.
