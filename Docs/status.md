# Project Status

## MB10-VL Sequential IN/OUT `.DAT` Processor

### Current Version

`v0.2.0`

### Status

Desktop UI added. The application now has a tkinter-based offline interface for selecting `.dat` files, previewing raw records, assigning IN/OUT statuses, and exporting CSV.

### Implemented

- [x] Project blueprint documented in `Docs/MB10-VL_Sequential_IN_OUT_Dev_Blueprint.md`
- [x] Agent instructions established in `AGENTS.md`
- [x] Core `.dat` parser (`src/lgus_dat/parser/dat_parser.py`)
- [x] Attendance sequence processor (`src/lgus_dat/processing/sequence_processor.py`)
- [x] CSV output writer (`src/lgus_dat/output/csv_writer.py`)
- [x] CLI entry point (`src/lgus_dat/cli/commands.py`)
- [x] Automated tests (`tests/test_processor.py`)
- [x] Packaging configuration (`pyproject.toml`, `requirements.txt`)
- [x] Desktop tkinter UI (`src/lgus_dat/ui/app.py`) with open/process/save workflow

### In Progress

- [ ] End-to-end processing of real MB10-VL exports
- [ ] Duplicate detection and exception reporting
- [ ] Desktop/offline distribution packaging

### Version History

| Version | Date | Notes |
| ------- | ---- | ----- |
| v0.0.1 | 2026-08-12 | Initial blueprint and project scaffolding added. |
| v0.1.0 | 2026-08-12 | Python package scaffold with parser, processor, CLI, and tests. |
| v0.2.0 | 2026-08-12 | Desktop tkinter UI for open/process/save workflow. |

Bump the version in this file whenever a significant milestone, feature, or release is completed.
