"""UI controller for business logic coordination."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Optional

from lgus_dat.domain.attendance_record import AttendanceRecord, PunchStatus
from lgus_dat.importers.department_parser import parse_department_dat
from lgus_dat.importers.user_parser import parse_user_dat
from lgus_dat.output.attlog_writer import write_attlog
from lgus_dat.output.csv_writer import write_csv
from lgus_dat.output.pdf_writer import generate_dtr_pdf, group_records_by_employee
from lgus_dat.parser.dat_parser import ParsedRecord, parse_dat_file
from lgus_dat.persistence.registry import AttendanceRegistry
from lgus_dat.processing.sequence_processor import process_records
from lgus_dat.ui.date_filter import filter_by_date
from lgus_dat.ui.search_filter import filter_by_search


@dataclass
class UIState:
    """State container for UI application."""
    current_input_path: Optional[Path] = None
    parsed_records: list[ParsedRecord] = field(default_factory=list)
    all_processed_records: list[AttendanceRecord] = field(default_factory=list)
    processed_records: list[AttendanceRecord] = field(default_factory=list)
    filter_start: Optional[datetime] = None
    filter_end: Optional[datetime] = None
    search_query: str = ""


class UIController:
    """Controller for coordinating business logic operations."""

    def __init__(self, registry: AttendanceRegistry) -> None:
        self.registry = registry
        self.state = UIState()

    def load_file(self, path: Path) -> tuple[Path, list[ParsedRecord], list[Any], int]:
        """Load and parse a .DAT file.
        
        Args:
            path: Path to the .DAT file
            
        Returns:
            Tuple of (path, records, errors, new_count)
        """
        records, errors = parse_dat_file(path)
        new_count = 0
        if records:
            new_count = self.registry.import_attendance_logs(records, path)
        
        self.state.current_input_path = path
        self.state.parsed_records = records
        
        return path, records, errors, new_count

    def process_records(
        self,
        records: Optional[list[ParsedRecord]] = None,
        name_lookup: Optional[Callable[[str], Optional[str]]] = None,
    ) -> list[AttendanceRecord]:
        """Process attendance records to assign IN/OUT status.
        
        Args:
            records: Optional list of records to process (uses state if None)
            name_lookup: Optional function to lookup employee names
            
        Returns:
            List of processed attendance records
        """
        if records is None:
            records = self.state.parsed_records
        
        if name_lookup is None:
            name_lookup = self.registry.employee_name
        
        self.state.all_processed_records = process_records(records, name_lookup=name_lookup)
        self._apply_filters()
        
        return self.state.all_processed_records

    def load_from_db(self) -> list[ParsedRecord]:
        """Load attendance logs from the database.
        
        Returns:
            List of parsed records from database
        """
        logs = self.registry.get_attendance_logs()
        self.state.current_input_path = None
        self.state.parsed_records = logs
        return logs

    def apply_date_filter(
        self,
        start: Optional[datetime],
        end: Optional[datetime],
    ) -> tuple[int, int]:
        """Apply date/time filter to records.
        
        Args:
            start: Optional start datetime
            end: Optional end datetime
            
        Returns:
            Tuple of (input_count, output_count) after filtering
        """
        self.state.filter_start = start
        self.state.filter_end = end
        self._apply_filters()
        
        input_count = len(self._get_filtered_parsed_records())
        output_count = len(self.state.processed_records)
        
        return input_count, output_count

    def apply_search_filter(self, query: str) -> tuple[int, int]:
        """Apply search filter to records.
        
        Args:
            query: Search query string
            
        Returns:
            Tuple of (input_count, output_count) after filtering
        """
        self.state.search_query = query
        self._apply_filters()
        
        input_count = len(self._get_filtered_parsed_records())
        output_count = len(self.state.processed_records)
        
        return input_count, output_count

    def clear_filters(self) -> tuple[int, int]:
        """Clear all filters.
        
        Returns:
            Tuple of (input_count, output_count) after clearing
        """
        self.state.filter_start = None
        self.state.filter_end = None
        self.state.search_query = ""
        self._apply_filters()
        
        input_count = len(self._get_filtered_parsed_records())
        output_count = len(self.state.processed_records)
        
        return input_count, output_count

    def _apply_filters(self) -> None:
        """Apply current filters to process records."""
        # Filter parsed records
        filtered_parsed = filter_by_date(
            self.state.parsed_records,
            lambda rec: rec.timestamp,
            self.state.filter_start,
            self.state.filter_end,
        )
        filtered_parsed = filter_by_search(
            filtered_parsed,
            self.state.search_query,
            [
                lambda rec: rec.employee_id,
                lambda rec: self.registry.employee_name(rec.employee_id) or "",
            ],
        )
        
        # Filter processed records
        filtered_processed = filter_by_date(
            self.state.all_processed_records,
            lambda rec: rec.timestamp,
            self.state.filter_start,
            self.state.filter_end,
        )
        # For processed records, use the stored employee_name if available, otherwise look it up
        filtered_processed = filter_by_search(
            filtered_processed,
            self.state.search_query,
            [
                lambda rec: rec.employee_id,
                lambda rec: rec.employee_name if rec.employee_name else self.registry.employee_name(rec.employee_id) or "",
            ],
        )
        
        self.state.processed_records = filtered_processed

    def _get_filtered_parsed_records(self) -> list[ParsedRecord]:
        """Get currently filtered parsed records."""
        filtered = filter_by_date(
            self.state.parsed_records,
            lambda rec: rec.timestamp,
            self.state.filter_start,
            self.state.filter_end,
        )
        return filter_by_search(
            filtered,
            self.state.search_query,
            [
                lambda rec: rec.employee_id,
                lambda rec: self.registry.employee_name(rec.employee_id) or "",
            ],
        )

    def edit_record_status(
        self,
        old_record: AttendanceRecord,
        new_status: PunchStatus,
    ) -> Optional[AttendanceRecord]:
        """Edit the status of a specific record.
        
        Args:
            old_record: The record to edit
            new_status: The new status to assign
            
        Returns:
            The edited record, or None if not found
        """
        from dataclasses import replace
        
        edited = replace(old_record, status=new_status, exception_flag="MANUAL_EDIT")
        
        try:
            index = self.state.all_processed_records.index(old_record)
            self.state.all_processed_records[index] = edited
            self._apply_filters()  # Reapply filters to update processed_records
            return edited
        except ValueError:
            return None

    def save_csv(self, path: Path) -> int:
        """Save processed records to CSV.
        
        Args:
            path: Output file path
            
        Returns:
            Number of records saved
        """
        write_csv(self.state.processed_records, path)
        return len(self.state.processed_records)

    def export_attlog(self, path: Path) -> int:
        """Export processed records to attlog.dat format.
        
        Args:
            path: Output file path
            
        Returns:
            Number of records exported
        """
        write_attlog(self.state.processed_records, path)
        return len(self.state.processed_records)

    def generate_dtr_pdf(
        self,
        selection: dict,
        month: date,
        path: Path,
    ) -> tuple[str, int]:
        """Generate DTR PDF report.
        
        Args:
            selection: Selection dictionary from PDF dialog
            month: Month for the report
            path: Output file path
            
        Returns:
            Tuple of (path, record_count)
        """
        # Filter records based on selection
        filtered_records = self._filter_records_for_dtr(selection, self.state.all_processed_records)
        
        # Get employee names and department info
        # Use full_name for DTR report if available; otherwise fall back to name.
        employee_names = {
            emp.device_user_id: (emp.full_name or emp.name)
            for emp in self.registry.all_employees()
        }
        department_names = {dept.department_id: dept.name for dept in self.registry.all_departments()}
        employee_departments = {
            emp.device_user_id: emp.department_id 
            for emp in self.registry.all_employees() 
            if emp.department_id is not None
        }

        # Group records by employee
        grouped = group_records_by_employee(filtered_records)

        generate_dtr_pdf(
            employee_records=grouped,
            month=month,
            output_path=path,
            employee_names=employee_names,
            department_names=department_names,
            employee_departments=employee_departments,
        )
        
        return str(path), len(filtered_records)

    def _filter_records_for_dtr(
        self,
        selection: dict,
        records: list[AttendanceRecord],
    ) -> list[AttendanceRecord]:
        """Filter attendance records based on DTR selection."""
        mode = selection["mode"]
        
        if mode == "all":
            return records
        
        filtered = []
        if mode == "employees":
            employee_ids = set(selection["employee_ids"])
            filtered = [r for r in records if r.employee_id in employee_ids]
        elif mode == "departments":
            department_ids = set(selection["department_ids"])
            # Get employees in selected departments
            employee_ids = set()
            for emp in self.registry.all_employees():
                if emp.department_id in department_ids:
                    employee_ids.add(emp.device_user_id)
            filtered = [r for r in records if r.employee_id in employee_ids]
        
        return filtered

    def import_user_dat(self, path: Path) -> tuple[list[Any], list[Any], int]:
        """Import user.dat file.
        
        Args:
            path: Path to user.dat file
            
        Returns:
            Tuple of (employees, errors, count)
        """
        employees, errors = parse_user_dat(path)
        if errors:
            return employees, errors, 0
        count = self.registry.import_employees(employees)
        return employees, errors, count

    def import_department_dat(self, path: Path) -> tuple[list[Any], list[Any], int]:
        """Import department.dat file.
        
        Args:
            path: Path to department.dat file
            
        Returns:
            Tuple of (departments, errors, count)
        """
        departments, errors = parse_department_dat(path)
        if errors:
            return departments, errors, 0
        count = self.registry.import_departments(departments)
        return departments, errors, count

    def get_registry_info(self) -> tuple[str, int, int]:
        """Get registry information.
        
        Returns:
            Tuple of (db_path, employee_count, log_count)
        """
        with self.registry._connection() as conn:
            employee_count = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        
        log_count = self.registry.count_attendance_logs()
        source_count = len(self.registry.get_attendance_log_sources())
        
        return str(self.registry.db_path), employee_count, log_count

    def get_employee_name(self, employee_id: str) -> Optional[str]:
        """Get employee name by ID."""
        return self.registry.employee_name(employee_id)


class ProgressRunner:
    """Helper class for running operations with progress dialogs."""

    def __init__(self, parent: tk.Tk) -> None:
        self.parent = parent
        self.dialog: Optional[Any] = None

    def run_with_progress(
        self,
        title: str,
        target: Callable[[], Any],
        on_done: Callable[[Any], None],
    ) -> None:
        """Run target in background thread with progress dialog.
        
        Args:
            title: Title for progress dialog
            target: Function to run in background
            on_done: Callback when target completes
        """
        from lgus_dat.ui.components.progress_dialog import ProgressDialog
        
        self.dialog = ProgressDialog(self.parent, title)
        result_queue: queue.Queue[tuple[bool, Any]] = queue.Queue()

        def worker() -> None:
            try:
                result = target()
                result_queue.put((True, result))
            except Exception as exc:
                result_queue.put((False, exc))

        def poll() -> None:
            try:
                success, result = result_queue.get_nowait()
            except queue.Empty:
                self.parent.after(100, poll)
                return

            self.dialog.close()
            if success:
                on_done(result)
            else:
                from tkinter import messagebox
                messagebox.showerror("Error", str(result), parent=self.parent)

        threading.Thread(target=worker, daemon=True).start()
        self.parent.after(100, poll)