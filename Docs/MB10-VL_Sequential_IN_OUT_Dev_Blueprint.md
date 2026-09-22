# MB10-VL Sequential IN/OUT `.DAT` Processor --- Development Blueprint

## 1. Project Objective

Build an HR-focused attendance management and DTR (Daily Time Record)
generation application that consumes raw `.dat` attendance exports from a
ZKTeco MB10-VL biometric terminal and assigns attendance status by punch
sequence.

The application stores imported attendance data, employee records, and
department records in a local persistence layer so that data does not
need to be re-imported on every launch. HR users can process attendance,
filter and search records, and generate printable DTR reports or exports
for payroll and record-keeping.

The required business rule is:

The required business rule is:

-   1st punch of an employee on a given calendar date = `IN`
-   2nd punch = `OUT`
-   3rd punch = `IN`
-   4th punch = `OUT`
-   Continue alternating for subsequent punches.

The MB10-VL itself should **not** be responsible for deciding IN/OUT.
Its punch-state functionality will be disabled, and the application will
derive the status from chronological punch order.

------------------------------------------------------------------------

## 2. Device Configuration

Configure the MB10-VL as follows:

  Setting                Value
  ---------------------- ------------
  Punch State Mode       `OFF`
  Punch State Required   `OFF`
  Auto Mode              Do not use
  Manual and Auto Mode   Do not use
  Fixed Mode             Do not use

### Rationale

`Punch State Mode = OFF` disables the device punch-state function.

`Punch State Required = OFF` means the employee does not have to select
an attendance state after biometric verification.

The terminal should therefore record raw verification/punch events
without requiring the user to choose IN or OUT.

The application determines IN/OUT later from the chronological sequence.

------------------------------------------------------------------------

## 3. Input Format

The current sample `.dat` file supplied during design contained records
similar to:

``` text
2    2026-08-12 08:03:27    1    0    15    0
2    2026-08-12 08:05:12    1    0    15    0
```

The application must initially support this whitespace-delimited
structure.

### Known fields from the sample

``` text
Field 1: Employee/User ID
Field 2: Date
Field 3: Time
Field 4: Additional device field
Field 5: Additional device field
Field 6: Additional device field
Field 7: Additional device field
```

The exact semantic meaning of fields 4--7 should **not be assumed unless
verified against the MB10-VL documentation or additional test exports**.

The processor must preserve the original fields rather than destroying
information.

### Important parsing requirement

Do not split the date and time into unrelated records. Combine them into
a single timestamp:

``` text
2026-08-12 08:03:27
```

Use a proper datetime value internally.

------------------------------------------------------------------------

## 4. Core Business Logic

### Grouping

Records must be grouped by:

1.  Employee/User ID
2.  Calendar date

Within each group, sort records by timestamp ascending.

### Status assignment

For each employee/date group:

``` text
record index 0 -> IN
record index 1 -> OUT
record index 2 -> IN
record index 3 -> OUT
record index 4 -> IN
record index 5 -> OUT
...
```

Equivalent rule:

``` text
if zero_based_index % 2 == 0:
    status = IN
else:
    status = OUT
```

### Example

Input:

``` text
Employee 1001
2026-08-12 07:58:12
2026-08-12 12:01:04
2026-08-12 13:02:19
2026-08-12 17:06:31
```

Output:

``` text
Employee 1001 | 2026-08-12 07:58:12 | IN
Employee 1001 | 2026-08-12 12:01:04 | OUT
Employee 1001 | 2026-08-12 13:02:19 | IN
Employee 1001 | 2026-08-12 17:06:31 | OUT
```

------------------------------------------------------------------------

## 5. Sequence Must Be Independent Per Employee

Never alternate statuses globally across the entire file.

Example:

``` text
Employee 1
  08:00 -> IN
  12:00 -> OUT
  13:00 -> IN
  17:00 -> OUT

Employee 2
  08:10 -> IN
  12:05 -> OUT
  13:05 -> IN
  17:10 -> OUT
```

Employee 2 must start at `IN` regardless of how many records Employee 1
has.

------------------------------------------------------------------------

## 6. Sequence Must Reset Each Calendar Day

The sequence starts over for each employee on each calendar date.

Example:

``` text
2026-08-12
  08:00 -> IN
  17:00 -> OUT

2026-08-13
  08:01 -> IN
  17:01 -> OUT
```

Do not carry an odd/even state from one day into the next.

------------------------------------------------------------------------

## 7. Duplicate Punches

The application should detect duplicate records.

A duplicate should be defined conservatively as records having the same:

-   Employee ID
-   Timestamp
-   Original record identity/content, where available

Do **not** automatically discard near-duplicates such as:

``` text
08:03:27
08:03:29
```

unless an explicit configurable duplicate window is introduced.

This is important because two rapid biometric verifications may be
legitimate raw events.

### Recommended initial behavior

-   Preserve all source records.
-   Do not silently delete records.
-   Report exact duplicates separately.
-   Make duplicate handling configurable in a later version.

### Duplicate punch status assignment

For the purpose of assigning `IN`/`OUT` status, consecutive records that
share the exact same timestamp are treated as a single punch event. All
records in such a group receive the status that the first record in the
group would have received under the normal alternating sequence. The
sequence then continues with the next distinct timestamp as if the group
consumed one punch position.

This preserves all source records while preventing the same physical
verification from being alternated `IN` / `OUT` / `IN` / `OUT`.

------------------------------------------------------------------------

## 8. Odd Number of Daily Punches

An employee may have an odd number of punches:

``` text
08:00 -> IN
12:00 -> OUT
13:00 -> IN
```

This means there is no matching OUT punch for the final IN.

The processor should **not invent a missing OUT time**.

Instead:

-   assign the final record `IN`
-   flag the employee/date as `UNPAIRED`
-   include it in an exception report

Example:

``` text
Employee: 1001
Date: 2026-08-12
Punches: 3
Status: UNPAIRED_FINAL_IN
```

This allows payroll/attendance staff to investigate rather than hiding
an anomaly.

------------------------------------------------------------------------

## 9. First Version Output

The application should produce a processed attendance output containing
at minimum:

``` text
Employee ID
Date
Time
Timestamp
Status
Original Record
Exception Flag
```

Example:

``` text
1001 | 2026-08-12 | 07:58:12 | 2026-08-12 07:58:12 | IN  | <original> | 
1001 | 2026-08-12 | 12:01:04 | 2026-08-12 12:01:04 | OUT | <original> |
1001 | 2026-08-12 | 13:02:19 | 2026-08-12 13:02:19 | IN  | <original> |
1001 | 2026-08-12 | 17:06:31 | 2026-08-12 17:06:31 | OUT | <original> |
```

The original source data should remain recoverable.

------------------------------------------------------------------------

## 10. Preserve the Original `.DAT`

Never modify the source `.dat` file in place.

Recommended workflow:

``` text
/input/
    attendance.dat

/output/
    attendance_processed.csv

/archive/
    original attendance.dat
```

If the application has an import workflow, it should copy/archive the
original file before processing.

------------------------------------------------------------------------

## 11. Idempotency

The same `.dat` file should be safe to process more than once.

Processing the same input twice must produce the same output and must
not double the attendance records.

If a database is used, create a deterministic record identity based on
the original source record and/or a stable hash.

------------------------------------------------------------------------

## 12. Timestamp Handling

Use the device timestamp as the source of truth.

Requirements:

-   Parse the timestamp strictly.
-   Sort chronologically.
-   Preserve seconds.
-   Do not round timestamps.
-   Do not silently convert time zones.
-   Make the application timezone configurable if needed.

For the initial deployment, assume the device and processing machine use
the same local timezone unless configuration says otherwise.

------------------------------------------------------------------------

## 13. Validation

Before processing, validate:

-   File exists.
-   File is readable.
-   Each non-empty record has the expected minimum number of fields.
-   Employee ID is present.
-   Date is valid.
-   Time is valid.
-   Timestamp is parseable.

Malformed records should be reported rather than causing the entire file
to fail.

Example error:

``` text
Line 42:
Invalid timestamp: 2026-99-99 25:61:00
```

Continue processing valid records unless the error rate exceeds a
configurable threshold.

------------------------------------------------------------------------

## 14. Recommended Architecture

Keep the core business logic independent from the user interface.

Suggested modules:

``` text
src/
  parser/
    dat_parser
  domain/
    attendance_record
    punch_sequence
  processing/
    sequence_processor
    duplicate_detector
    exception_detector
  output/
    csv_writer
    dat_writer (if required)
    pdf_writer
  cli/
    commands
  core/                # Shared application controller and filters
    controller
    date_filter
    search_filter
  desktop/             # PySide6 desktop UI
    app.py
    main_window.py
    pages/
    widgets/
    theme.py
  persistence/
    registry
  tests/
```

The legacy Tkinter `ui/` package has been removed; the PySide6
`desktop/` package is the only UI. Shared application logic
(`controller`, `date_filter`, `search_filter`) lives in `core/` so it
can be reused by future interfaces. The parser, domain, processing,
and output layers remain unchanged.

The exact programming language/framework is up to the developer unless
the surrounding project already dictates one.

------------------------------------------------------------------------

## 15. Core Processing Pseudocode

``` text
records = parse_dat_file(input_file)

valid_records, invalid_records = validate(records)

groups = group_by(
    valid_records,
    employee_id,
    calendar_date
)

for each group:
    sort group by timestamp ascending

    for index, record in enumerate(group):
        if index % 2 == 0:
            record.status = IN
        else:
            record.status = OUT

    if len(group) % 2 == 1:
        mark group as UNPAIRED_FINAL_IN

write_processed_output(records)
write_exception_report(invalid_records, exceptions)
```

------------------------------------------------------------------------

## 16. Test Cases

The developer must create automated tests for at least the following.

### Test 1 --- Two punches

``` text
08:00
17:00
```

Expected:

``` text
08:00 IN
17:00 OUT
```

### Test 2 --- Four punches

``` text
08:00
12:00
13:00
17:00
```

Expected:

``` text
08:00 IN
12:00 OUT
13:00 IN
17:00 OUT
```

### Test 3 --- Six punches

Expected:

``` text
1 IN
2 OUT
3 IN
4 OUT
5 IN
6 OUT
```

### Test 4 --- Odd number of punches

``` text
08:00
12:00
13:00
```

Expected:

``` text
08:00 IN
12:00 OUT
13:00 IN
```

And exception:

``` text
UNPAIRED_FINAL_IN
```

### Test 5 --- Multiple employees

Verify that each employee starts their own sequence at `IN`.

### Test 6 --- Multiple dates

Verify that the sequence resets at midnight/date boundary.

### Test 7 --- Unsorted input

Input:

``` text
17:00
08:00
12:00
```

Expected after sorting:

``` text
08:00 IN
12:00 OUT
17:00 IN
```

### Test 8 --- Exact duplicate

Verify that duplicates are detected/reported without silently deleting
source information.

### Test 9 --- Malformed record

Verify that a bad line is reported while valid records continue
processing.

### Test 10 --- Same timestamp

Two records for the same employee with identical timestamps must have a
deterministic ordering. Preserve source-file order as the tie-breaker.

------------------------------------------------------------------------

## 17. Important Business Rule: Do Not Add "Smart" Attendance Logic Yet

The first version should **not** automatically infer:

-   lunch breaks
-   overtime
-   missed punches
-   overnight shifts
-   grace periods
-   minimum punch intervals
-   duplicate suppression windows
-   shift schedules
-   holidays

Those are separate business rules.

The initial processor has one deliberately simple rule:

> **For each employee and calendar date, sort raw punches
> chronologically and alternate IN/OUT starting with IN.**

Keep this rule deterministic and auditable.

------------------------------------------------------------------------

## 18. DTR Undertime Calculation

When generating the DTR PDF, the application calculates daily undertime for
weekday workdays against the government DTR schedule.

### Official Weekday Schedule

-   **8:00 AM** — morning arrival
-   **12:00 PM** — lunch out
-   **1:00 PM** — lunch in
-   **5:00 PM** — afternoon departure

### Rules

-   Undertime is calculated only for **Monday-Friday**.
-   A weekday with **no punches at all** = **8 hours** undertime.
-   **Late arrival**: arrival after 8:00 AM = whole minutes late
    (e.g., 8:01 AM = 1 minute, 8:05 AM = 5 minutes).
-   **Early lunch out**: lunch out before 12:00 PM = whole minutes early
    (e.g., 11:35 AM = 25 minutes).
-   **Late lunch in**: lunch in after 1:00 PM = whole minutes late
    (e.g., 2:02 PM = 62 minutes).
-   **Early end**: departure before 5:00 PM = whole minutes early
    (e.g., 4:55 PM = 5 minutes, 4:50 PM = 10 minutes).
-   The last available PM departure is used for early end calculation; for
    two-punch days the AM departure is used as the final departure.
-   The total undertime for the day is displayed in the **Undertime Hr** and
    **Undertime Min** columns of the DTR.
-   At the bottom of the DTR, a **TOTAL =** row sums the **Hr** and **Min**
    columns separately and displays the monthly totals.
-   A **system-wide holiday** has no undertime.

### Notes

-   This is a fixed, deterministic rule and does not include grace periods
    or shift schedules.
-   Weekends (Saturdays and Sundays) show no undertime.

------------------------------------------------------------------------

## 19. Future Considerations

The architecture should leave room for:

-   employee master data
-   department/branch mapping
-   shift schedules
-   overnight shifts
-   configurable sequence reset rules
-   duplicate detection windows
-   manual correction workflow
-   payroll export
-   Excel/CSV export
-   database storage
-   web UI
-   audit trail
-   import history
-   multiple MB10-VL devices
-   device-specific parsers
-   configurable status labels

Do not implement these unless required by the initial project.

------------------------------------------------------------------------

## 19. Acceptance Criteria

The project is considered successful when:

1.  A raw MB10-VL `.dat` file can be imported.
2.  Employee IDs and timestamps are correctly parsed.
3.  Records are sorted chronologically per employee/date.
4.  The first punch is assigned `IN`.
5.  The second punch is assigned `OUT`.
6.  The sequence continues `IN/OUT` alternately.
7.  Each employee has an independent sequence.
8.  Each calendar date starts a new sequence.
9.  Odd punch counts are flagged rather than silently corrected.
10. Malformed records are reported.
11. Original source data is preserved.
12. Reprocessing the same file does not duplicate data.
13. Automated tests cover the core rules.
14. The processor can produce a clean output suitable for integration
    with the existing attendance/payroll system.
15. The PySide6 desktop UI is functional and visually modern.
16. Imported data persists across application restarts.
17. The application provides printable DTR reports and export options.
18. The UI supports a manual light/dark theme toggle.
19. Dashboard KPIs display useful summary metrics.

------------------------------------------------------------------------

## 20. Development Instruction for Devin

Build the application around the following principle:

> **The ZKTeco MB10-VL is a raw punch collector. The application is the
> source of truth for sequential IN/OUT assignment.**

Do not depend on the device's Automatic Status Switch for the core
business rule.

The device configuration is:

``` text
Punch State Mode     = OFF
Punch State Required = OFF
```

The application rule is:

``` text
GROUP BY employee_id + calendar_date
SORT BY timestamp ASCENDING

1st punch = IN
2nd punch = OUT
3rd punch = IN
4th punch = OUT
...

Odd final punch = flag as UNPAIRED_FINAL_IN
```

Keep the implementation deterministic, testable, auditable, and capable
of preserving the original `.dat` records.

Before implementing assumptions about fields 4--7 of the `.dat` format,
inspect additional real MB10-VL exports and confirm their meaning.

------------------------------------------------------------------------

## 21. Application Scope (Updated)

The application is intended primarily for HR staff. Its daily workflow is:

1.  Import attendance `.dat` files exported from the MB10-VL device.
2.  Optionally import `user.dat` and `department.dat` files.
3.  Process imported attendance records to assign `IN`/`OUT` statuses.
4.  Filter, search, and review processed records.
5.  Generate printable DTR (Daily Time Record) reports or export data for
    payroll and record-keeping.

Imported attendance data, employee data, and department data are stored
in a local persistence layer. Re-opening the application should not
require re-importing files that have already been loaded once, unless the
underlying data has changed.

------------------------------------------------------------------------

## 22. User Interface Architecture

The desktop user interface is being rebuilt in **PySide6** to provide a
modern dashboard-style experience with manual light/dark theme toggling.

### Framework

-   **PySide6** for the desktop UI (LGPL, compatible with distribution)
-   Existing **Tkinter** UI is kept in parallel during the migration
-   **PyInstaller** for the final packaged executable
-   Core parser, processor, and persistence layers remain unchanged

### UI Layout

``` text
Main Window
|-- Sidebar navigation
|   |-- Dashboard
|   |-- Import
|   |-- Processed Records
|   |-- Daily DTR Review
|   |-- Attendance Filing
|   |-- Reports
|   |-- Employees
|   |-- Settings
|
|-- Content area (stacked pages)
|   |-- Dashboard page: KPI cards and quick actions
|   |-- Import page: file import and raw input preview
|   |-- Processed Records page: IN/OUT output, filters, search
|   |-- Daily DTR Review page: employee list, month DTR preview, daily punch
|   |   editor with IN/OUT status editing, manual DTR slot overrides, and a
|   |   per-employee Export DTR PDF button
|   |-- Attendance Filing page: holidays, leave types, employee filings
|   |-- Reports page: DTR PDF, CSV, attlog export
|   |-- Employees page: employee and department management, including department head name and position on the DTR signature line
|
|-- Status bar
```

### Theme

-   Manual light/dark mode toggle in the main window or settings
-   Theme state persisted in user settings
-   All custom widgets and pages respect the active theme

### Search and Filter Behavior

-   Search is triggered by a button click (not real-time typing)
-   Date and time filters use `QDateEdit` and `QTimeEdit` pickers
-   Filters apply to both input and processed record views
-   Name lookup is cached in memory to avoid repeated database access

------------------------------------------------------------------------

## 23. Dashboard KPIs

The dashboard page should display summary cards for at least the
following metrics:

-   Total employees
-   Total attendance records imported
-   Total processed records
-   Unpaired `IN` records (odd punch counts)
-   Parse/import errors (if any)
-   Selected month for DTR report

Additional KPIs may be added as the project evolves.

------------------------------------------------------------------------

## 24. Performance Targets

The PySide6 UI should be more responsive than the previous Tkinter
implementation. Specific targets include:

-   Cached employee name lookups during filtering and display
-   `QTableView` with `QAbstractTableModel` for large record lists
-   Debounced or button-triggered search to avoid re-filtering on every
    keystroke
-   Only re-apply filters when the query or filter values change
-   Progress dialogs for long-running operations (import, process,
    export, report generation)

------------------------------------------------------------------------

## 25. Migration Plan

The migration from Tkinter to PySide6 is executed in the following
phases. The Tkinter UI is kept in parallel until the PySide6 UI is
complete.

| Phase | Work | Deliverable |
|-------|------|-------------|
| 0     | Add PySide6 dependency and create `desktop/` package | Basic working PySide6 window |
| 1     | Build dashboard shell: sidebar, stacked pages, theme | Navigable skeleton with light/dark mode |
| 2     | Port import and input preview | Can import `.dat` and view raw records |
| 3     | Port processing, filters, search | Full process and filter workflow |
| 4     | Port reports and exports | DTR PDF, CSV, attlog export working |
| 5     | Port employee/department management | Management dialogs and pages |
| 6     | Polish: KPI cards, charts, packaging | Final modern app |
| 7     | Remove Tkinter UI and update docs | Completed: `core/` for shared logic, only PySide6 UI |

------------------------------------------------------------------------

## 26. Future Considerations (Updated)

The following features are out of scope for the initial redesign but
may be added as the project evolves:

-   Real-time search as the user types
-   Data visualization charts (charts and trends)
-   Automatic sync with the device
-   Multi-terminal support
-   Web-based or mobile companion
-   Advanced payroll export formats
-   Shift schedules and overtime rules

------------------------------------------------------------------------

## 27. Attendance Filing and DTR Remarks

The PySide6 desktop UI provides an **Attendance Filing** page where HR users can
configure attendance statuses that modify the DTR `Remarks` column.

### Holiday master (system-wide)

-   Stored in the `holidays` table (`holiday_date` primary key, `name`).
-   Affects every employee on that calendar date.
-   Managed from the **Holidays** tab under **Attendance Filing**.

### Leave / attendance status types

-   Stored in the `leave_types` table, similar to the `positions` master list.
-   Pre-populated with `Leave`, `Sick Leave`, `Fieldwork`, `Holiday`.
-   CRUD is available in the **Leave Types** tab.

### Employee status filing

-   Stored in the `employee_status_filings` table.
-   Each filing links an employee, a start and end date, and a status type.
-   Consecutive days are supported via a date range.
-   The **File Leave/Status** tab lets the user pick an employee, a range, and
    a status.

### DTR output

-   The DTR `Remarks` column falls back to the abbreviated weekday (MON, TUE,
    etc.) when no holiday or filing exists.
-   When a system-wide holiday applies, the holiday name is printed.
-   When an employee has a filed status, the status type name is printed.
-   If both apply to the same day, they are combined with ` / `.
-   Any biometric punches for that day are still printed in the AM/PM time
    slots.
-   A day filed with any leave/status type has no undertime calculated,
    regardless of the biometric punches recorded.

### DTR Manual Slot Overrides

-   The DTR preview and PDF generation map raw punches to the `in_am`, `out_am`,
    `in_pm`, and `out_pm` time slots using the default four-punch rule.
-   The **Daily DTR Review** page allows the user to manually override any of
    these four slots for a selected employee and date.
-   The override stores the selected punch time for the slot without changing
    the underlying `IN`/`OUT` status assignment.
-   Overrides are persisted in the `dtr_slot_overrides` table and are applied
    when generating the DTR preview or PDF.
-   If an override is cleared or the slot is empty, the default four-punch
    mapping is used for that slot.
-   The **Daily DTR Review** page also provides an **Export DTR PDF** button
    that generates a single-employee DTR PDF for the employee and month
    currently in view, so punch fixes and slot overrides can be exported
    without going through the Reports page scope dialog.

## 28. Distribution, Installation, and Data Storage

### Distribution Formats

-   **Full Windows installer (Inno Setup)**: Produces `LGUS-DAT-Setup-V{VERSION}.exe`, which installs the one-directory PyInstaller bundle into `%ProgramFiles%\LGUS-DAT`, creates Start Menu (and optional Desktop) shortcuts, and registers an uninstall entry.
-   **Patcher-only `.exe` (`dist/patcher/lgus-dat-patcher-V{VERSION}.exe`)**: A small updater that scans the Inno Setup uninstall registry key for an existing `LGUS-DAT` installation, prompts for administrator rights, and replaces the installed files with the bundled `dist/desktop/lgus-dat-desktop-V{VERSION}` payload, without running a full install.
-   **Portable ZIP / one-directory build**: `dist/desktop/lgus-dat-desktop-V{VERSION}` can be zipped and run from any writable location; intended for testing.
-   **MSIX package (future)**: For Microsoft Store submission or enterprise sideloading.

### Build Conventions

-   Before any build, confirm whether the current version needs a **full installer** or a **patcher-only `.exe`**.
-   The project version in `pyproject.toml` and `Docs/status.md` must match before building.
-   The PyInstaller one-directory bundle is named `lgus-dat-desktop-V{VERSION}` and is packaged by Inno Setup.
-   The patcher is built as `dist/patcher/lgus-dat-patcher-V{VERSION}.exe` from `installer/patcher.py` with `--onefile` and `--uac-admin`, bundling `dist/desktop/lgus-dat-desktop-V{VERSION}` as an `update` data archive.

### SQLite Registry (`lgus_registry.db`)

-   When the application is packaged/bundled (`sys.frozen`), `lgus_registry.db` is created next to the `.exe`, i.e., inside the installation directory. This keeps the database easy to find and back up manually.
-   When running from source, `lgus_registry.db` is created in the current working directory.
-   Because `%ProgramFiles%` is a protected directory, the installed `.exe` must be run with administrator rights to write the database. This is by design; the installer does **not** move the database to `%APPDATA%`.
