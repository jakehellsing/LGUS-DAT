# DTR PDF Generation Guide

## Overview

The LGUS-DAT application now includes DTR (Daily Time Record) PDF generation functionality for creating monthly attendance reports matching the government DTR form layout.

## Features

### Report Format

- **Government DTR form layout**: Each employee gets one physical page that contains two side-by-side copies of the same DTR.
- Each copy includes:
  - Centered `DAILY TIME RECORD` title
  - Employee `NAME:` and `For the Month of:` fields
  - Table columns with merged headers:
    - **Day** (1-31)
    - **AM** (Arrival, Departure)
    - **PM** (Arrival, Departure)
    - **Undertime** (Hr, Min)
    - **Remarks** (weekday abbreviation, or a holiday / leave status label)
  - `TOTAL =` line below the table showing the monthly totals in the **Undertime Hr** and **Undertime Min** columns
  - Certification text: *"I CERTIFY on my honor..."*
  - Signature line for the employee
  - Signature line for the department's `head_name` and `head_position`; `head_position` replaces the generic `Verifying Officer` label when set

### Data Processing
- **Holiday and leave status remarks**: System-wide holidays and per-employee filed status ranges are looked up for the report month. When present, the DTR `Remarks` cell prints the holiday name and/or status label instead of the weekday; both may be combined with ` / `.
- **Leave/status undertime**: A day filed with any leave/status type (e.g. `Fieldwork`, `Sick Leave`, `Vacation Leave`) has zero undertime, regardless of the recorded punches.
- **Holiday undertime**: A system-wide holiday has zero undertime, regardless of the recorded punches.
- **Duplicate handling**: When duplicate punches with the same employee_id, date, and timestamp are found, only the first occurrence is used
- **4-punch mapping**: The first 4 punches per day are mapped to the 4 time slots:
  - 1st punch → AM Arrival
  - 2nd punch → AM Departure
  - 3rd punch → PM Arrival
  - 4th punch → PM Departure
- **Undertime calculation**: For Monday-Friday workdays, undertime is calculated against the government DTR schedule:
  - 8:00 AM morning arrival
  - 12:00 PM lunch out
  - 1:00 PM lunch in
  - 5:00 PM afternoon departure
  - Late arrival, early lunch out, late lunch in, and early departure are all counted in whole minutes
  - A weekday with no punches at all = 8 hours undertime
  - System-wide holidays are excluded from undertime
  - Saturdays and Sundays are excluded
- **Incomplete records**: Days with fewer than 4 punches show blank cells for missing time slots (marked for investigation)
- **Extra punches**: Only the first 4 punches are used; additional punches are ignored

### Selection Options
- **All Employees**: Generate reports for all employees in the registry
- **Specific Employees**: Select individual employees by ID/name
- **By Department**: Generate reports for all employees in selected departments

## Usage

### GUI Workflow

1. **Process Attendance Data**
   - Open a `.DAT` file using "Open .DAT" button
   - Click "Process (F5)" to generate IN/OUT status
   - Or use "Process from DB" to process all stored logs

2. **Configure Report**
   - Select the desired month using the month picker in the "DTR PDF Report" section
   - Click "Generate DTR PDF" button

3. **Select Report Scope**
   - Choose report scope in the dialog:
     - **All Employees**: Include all employees
     - **Specific Employees**: Select individual employees from the list
     - **By Department**: Select departments to include all their employees

4. **Generate and Save**
   - Choose the output location and filename
   - The PDF will be generated with one physical page per employee, containing two side-by-side DTR copies

### Per-Employee Export (Daily DTR Review page)

The **Daily DTR Review** page provides an **Export DTR PDF** button for the
employee and month currently in view:

1. Select an employee in the left pane and pick the month in the dropdown.
2. Fix punches as needed (IN/OUT status edits, manual DTR slot overrides).
3. Click **Export DTR PDF** and choose the output location.

This produces the same single-employee DTR PDF as the Reports page with a
"Specific Employees" scope, but skips the scope dialog so corrected records
can be exported immediately.

### Technical Details

#### File Location
- PDF writer module: `src/lgus_dat/output/pdf_writer.py`
- Selection dialog: `src/lgus_dat/desktop/pages/reports_page.py`
- Per-employee export: `src/lgus_dat/desktop/pages/dtr_review_page.py`
- GUI integration: `src/lgus_dat/desktop/app.py`

#### Dependencies
- ReportLab 4.0.0+ for PDF generation
- Uses existing employee/department registry for name resolution

#### Data Flow
1. Processed attendance records are filtered by selected month
2. Records are grouped by employee
3. Duplicate records are removed (first occurrence kept)
4. Records are grouped by day and sorted by timestamp
5. First 4 punches per day are mapped to time slots
6. Undertime is calculated for weekday arrivals after 8:00 AM and departures before 5:00 PM
7. The department head name and position are resolved from the employee's department and printed on the signature line; the position replaces `Verifying Officer` when set
8. PDF is generated with the government DTR form layout (two copies per page)

## Example Scenarios

### Complete Day (4 punches)
```
Employee: 1001, Date: 2026-08-01
08:00:00 → AM Arrival
12:00:00 → AM Departure
13:00:00 → PM Arrival
17:00:00 → PM Departure
```
Result: All 4 time cells filled with HH:MM times

### Incomplete Day (2 punches)
```
Employee: 1001, Date: 2026-08-02
08:05:00 → AM Arrival
12:05:00 → AM Departure
```
Result: AM Arrival and AM Departure filled, PM cells blank

### Duplicate Punches
```
Employee: 1001, Date: 2026-08-03
08:00:00 → AM Arrival (duplicate)
08:00:00 → AM Arrival (duplicate - ignored)
12:00:00 → AM Departure
13:00:00 → PM Arrival
17:00:00 → PM Departure
```
Result: First 08:00:00 used, second duplicate ignored

## Future Enhancements

Potential improvements for future versions:
- Custom headers and footers with company information
- Summary statistics (total hours, late arrivals, early departures)
- Exception reporting for incomplete records
- Multiple month reports
- Custom time slot configurations
- Department-level summary pages
- Signature lines for approval