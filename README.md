# LGUS-DAT

MB10-VL Sequential IN/OUT `.DAT` Processor.

This project consumes raw `.dat` attendance exports from a ZKTeco MB10-VL biometric terminal and assigns `IN`/`OUT` status by chronological punch sequence.

## Core Rule

> For each employee and calendar date, sort raw punches chronologically and alternate `IN`/`OUT` starting with `IN`.

See `Docs/MB10-VL_Sequential_IN_OUT_Dev_Blueprint.md` for full requirements.

## Project Structure

```
src/
  lgus_dat/
    parser/         .DAT parsing
    importers/      Device master file importers
    persistence/    SQLite employee/department registry
    domain/         Attendance models
    processing/     Sequence logic
    output/         CSV writers
    cli/            Command-line entry point
    ui/             Desktop tkinter interface

tests/              Automated tests
Docs/               Blueprint and status
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

You can also import the device's `user.dat` to resolve employee names from numeric IDs and `department.dat` to build a department registry. Use **Manage Employees** to view, add, edit, or delete employees and departments, then export them back to the same ZKTeco/NGteco binary `user.dat` / `department.dat` formats for re-import into the device.
