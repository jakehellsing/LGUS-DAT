# DTR PDF Generation Guide

## Overview

The LGUS-DAT application now includes DTR (Daily Time Record) PDF generation functionality for creating monthly attendance reports with an excel-like table format.

## Features

### Report Format
- **Excel-like table layout**: Each employee gets one page per month with columns:
  - Day (1-31)
  - Time IN A.M.
  - Time OUT A.M.
  - Time IN P.M.
  - Time OUT P.M.

### Data Processing
- **Duplicate handling**: When duplicate punches with the same employee_id, date, and timestamp are found, only the first occurrence is used
- **4-punch mapping**: The first 4 punches per day are mapped to the 4 time slots:
  - 1st punch → Time IN A.M.
  - 2nd punch → Time OUT A.M.
  - 3rd punch → Time IN P.M.
  - 4th punch → Time OUT P.M.
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
   - The PDF will be generated with one page per employee

### Technical Details

#### File Location
- PDF writer module: `src/lgus_dat/output/pdf_writer.py`
- Selection dialog: `src/lgus_dat/ui/pdf_selection_dialog.py`
- GUI integration: `src/lgus_dat/ui/app.py`

#### Dependencies
- ReportLab 4.0.0+ for PDF generation
- Uses existing employee/department registry for name resolution

#### Data Flow
1. Processed attendance records are filtered by selected month
2. Records are grouped by employee
3. Duplicate records are removed (first occurrence kept)
4. Records are grouped by day and sorted by timestamp
5. First 4 punches per day are mapped to time slots
6. PDF is generated with excel-like table layout

## Example Scenarios

### Complete Day (4 punches)
```
Employee: 1001, Date: 2026-08-01
08:00:00 → Time IN A.M.
12:00:00 → Time OUT A.M.
13:00:00 → Time IN P.M.
17:00:00 → Time OUT P.M.
```
Result: All 4 cells filled with times

### Incomplete Day (2 punches)
```
Employee: 1001, Date: 2026-08-02
08:05:00 → Time IN A.M.
12:05:00 → Time OUT A.M.
```
Result: IN AM and OUT AM filled, IN PM and OUT PM blank

### Duplicate Punches
```
Employee: 1001, Date: 2026-08-03
08:00:00 → Time IN A.M. (duplicate)
08:00:00 → Time IN A.M. (duplicate - ignored)
12:00:00 → Time OUT A.M.
13:00:00 → Time IN P.M.
17:00:00 → Time OUT P.M.
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