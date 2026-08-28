"""Tkinter desktop application for processing MB10-VL .DAT files (Refactored)."""

from __future__ import annotations

import sys
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Optional

from tkcalendar import DateEntry

from lgus_dat.domain.attendance_record import AttendanceRecord, PunchStatus
from lgus_dat.parser.dat_parser import ParsedRecord
from lgus_dat.persistence.registry import AttendanceRegistry
from lgus_dat.ui.components.date_filter_panel import DateFilterPanel
from lgus_dat.ui.components.file_toolbar import FileToolbar
from lgus_dat.ui.components.pdf_report_panel import PDFReportPanel
from lgus_dat.ui.components.progress_dialog import ProgressDialog
from lgus_dat.ui.components.registry_toolbar import RegistryToolbar
from lgus_dat.ui.components.search_panel import SearchPanel
from lgus_dat.ui.controller import ProgressRunner, UIController
from lgus_dat.ui.dialogs.management_dialog import ManagementDialog
from lgus_dat.ui.dialogs.pdf_selection_dialog import DTRSelectionDialog
from lgus_dat.ui.dialogs.status_edit_dialog import StatusEditDialog
from lgus_dat.ui.views.input_preview import InputPreview
from lgus_dat.ui.views.output_preview import OutputPreview
from lgus_dat.ui.views.status_panel import StatusPanel


class ProcessorApp:
    """Main application class using modular UI components."""

    def __init__(self, root: tk.Tk, initial_file: Optional[Path] = None) -> None:
        self.root = root
        self.root.title("LGUS-DAT — MB10-VL Attendance Processor")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)

        # Initialize controller and state
        self.registry = AttendanceRegistry()
        self.controller = UIController(self.registry)
        self.progress_runner = ProgressRunner(root)

        # Build UI with modular components
        self._build_ui()
        self._update_labels()

        # Load initial file if provided
        if initial_file:
            self.root.after(
                100,
                lambda: self.progress_runner.run_with_progress(
                    "Loading .DAT",
                    lambda: self.controller.load_file(initial_file),
                    self._on_load_complete,
                ),
            )

    def _build_ui(self) -> None:
        """Build the UI using modular components."""
        # File operations toolbar
        self.file_toolbar = FileToolbar(
            self.root,
            on_open=self._open_file,
            on_process=self._process,
            on_process_from_db=self._process_from_db,
            on_save_csv=self._save_csv,
            on_export_attlog=self._export_attlog,
            on_edit_status=self._edit_selected_status,
            on_f5_process=self._process,
        )
        self.file_toolbar.pack(fill=tk.X)
        self.file_toolbar.bind_f5(self.root)

        # Registry operations toolbar
        self.registry_toolbar = RegistryToolbar(
            self.root,
            on_import_user=self._import_user_dat,
            on_import_department=self._import_department_dat,
            on_manage_employees=self._open_management,
        )
        self.registry_toolbar.pack(fill=tk.X)

        # Date filter panel
        self.date_filter = DateFilterPanel(
            self.root,
            on_apply_filter=self._apply_date_filter,
            on_clear_filter=self._clear_date_filter,
        )
        self.date_filter.pack(fill=tk.X, padx=8, pady=(0, 4))

        # Search panel
        self.search_panel = SearchPanel(
            self.root,
            on_search=self._apply_search_filter,
            on_clear=self._clear_search_filter,
        )
        self.search_panel.pack(fill=tk.X, padx=8, pady=(0, 4))

        # PDF report panel
        self.pdf_panel = PDFReportPanel(
            self.root,
            on_generate_pdf=self._generate_dtr_pdf,
        )
        self.pdf_panel.pack(fill=tk.X, padx=8, pady=(0, 4))

        # Information labels
        self.path_label = ttk.Label(self.root, text="No file selected", padding=8)
        self.path_label.pack(fill=tk.X)

        self.registry_label = ttk.Label(self.root, text="Registry: Loading...", padding=8)
        self.registry_label.pack(fill=tk.X)

        self.logs_label = ttk.Label(self.root, text="Stored logs: Loading...", padding=8)
        self.logs_label.pack(fill=tk.X)

        # Notebook with input preview and output
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # Input preview tab
        input_frame = ttk.Frame(notebook)
        notebook.add(input_frame, text="Input Preview")
        self.input_preview = InputPreview(input_frame)
        self.input_preview.pack(fill=tk.BOTH, expand=True)

        # Output preview tab
        output_frame = ttk.Frame(notebook)
        notebook.add(output_frame, text="Processed Output")
        self.output_preview = OutputPreview(output_frame)
        self.output_preview.pack(fill=tk.BOTH, expand=True)

        # Status panel
        self.status_panel = StatusPanel(self.root)
        self.status_panel.pack(fill=tk.X, padx=8, pady=(0, 8))

    def _update_labels(self) -> None:
        """Update information labels."""
        db_path, emp_count, log_count = self.controller.get_registry_info()
        source_count = len(self.registry.get_attendance_log_sources())
        
        self.registry_label.config(
            text=f"Registry: {db_path} — {emp_count} employees"
        )
        self.logs_label.config(
            text=f"Stored logs: {log_count} row(s) from {source_count} source(s)"
        )

    def _open_file(self) -> None:
        """Handle open file button click."""
        path = filedialog.askopenfilename(
            title="Select MB10-VL .DAT export",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")],
        )
        if not path:
            return
        
        self.progress_runner.run_with_progress(
            "Loading .DAT",
            lambda: self.controller.load_file(Path(path)),
            self._on_load_complete,
        )

    def _on_load_complete(self, result: tuple[Path, list[ParsedRecord], list[Any], int]) -> None:
        """Handle file load completion."""
        path, records, errors, new_count = result
        self.path_label.config(text=str(path))
        
        # Update input preview
        displayed = self.input_preview.load_records(
            records,
            name_lookup=self.controller.get_employee_name,
        )
        
        # Clear output preview
        self.output_preview.clear()
        
        self.status_panel.log(f"Opened {path}")
        if records:
            self.status_panel.log(f"Saved {new_count} new log row(s) to local DB ({len(records)} total in file).")

        if errors:
            self.status_panel.log(f"Found {len(errors)} parse error(s):")
            for err in errors:
                self.status_panel.log(str(err))
        else:
            self.status_panel.log(f"Parsed {len(records)} record(s) successfully. {displayed} shown with current filter.")
        
        self._update_labels()

    def _process(self) -> None:
        """Handle process button click."""
        if not self.controller.state.parsed_records:
            messagebox.showwarning("No data", "Open a .DAT file first.")
            return

        def process_sync():
            return self.controller.process_records()

        self.progress_runner.run_with_progress(
            "Processing attendance data",
            process_sync,
            self._on_process_complete,
        )

    def _on_process_complete(self, result: list[AttendanceRecord]) -> None:
        """Handle process completion."""
        # Update output preview
        displayed = self.output_preview.load_records(self.controller.state.processed_records)
        self.status_panel.log(f"Processed {len(self.controller.state.all_processed_records)} record(s). {displayed} shown with current filter.")

    def _process_from_db(self) -> None:
        """Handle process from DB button click."""
        def load_and_process_sync():
            logs = self.controller.load_from_db()
            if not logs:
                return None, []
            self.controller.process_records()
            return logs, self.controller.state.processed_records

        self.progress_runner.run_with_progress(
            "Loading and processing logs from DB",
            load_and_process_sync,
            self._on_process_from_db_complete,
        )

    def _on_process_from_db_complete(self, result: tuple[Optional[list[ParsedRecord]], list[AttendanceRecord]]) -> None:
        """Handle process from DB completion."""
        logs, processed = result
        if logs is None:
            messagebox.showwarning("No logs", "No attendance logs stored in the local DB. Import a .DAT file first.")
            return

        self.path_label.config(text="<all stored logs>")
        
        # Update input preview
        displayed_input = self.input_preview.load_records(
            logs,
            name_lookup=self.controller.get_employee_name,
        )
        
        # Update output preview
        displayed_output = self.output_preview.load_records(processed)
        
        self.status_panel.log(f"Loaded {len(logs)} log row(s) from DB. {displayed_input} shown with current filter.")
        self.status_panel.log(f"Processed {len(self.controller.state.all_processed_records)} record(s). {displayed_output} shown with current filter.")

    def _edit_selected_status(self) -> None:
        """Handle edit status button click."""
        selected_record = self.output_preview.get_selected_record()
        if not selected_record:
            messagebox.showwarning("No selection", "Select a processed output row to edit its status.")
            return

        dialog = StatusEditDialog(self.root, selected_record.status)
        new_status = dialog.get_result()
        
        if new_status is None or new_status == selected_record.status:
            return

        edited = self.controller.edit_record_status(selected_record, new_status)
        if edited:
            self.output_preview.update_record(selected_record, edited)
            self.status_panel.log(
                f"Manual edit: {selected_record.employee_id} at "
                f"{selected_record.timestamp.strftime('%Y-%m-%d %H:%M:%S')} changed from "
                f"{selected_record.status.value} to {edited.status.value}"
            )
        else:
            self.status_panel.log(f"Could not update {selected_record.employee_id} — original row not found.")

    def _save_csv(self) -> None:
        """Handle save CSV button click."""
        if not self.controller.state.processed_records:
            messagebox.showwarning("No output", "Process a file first or adjust the date filter.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        def save_sync():
            return self.controller.save_csv(Path(path))

        self.progress_runner.run_with_progress(
            "Saving CSV",
            save_sync,
            lambda count: self.status_panel.log(f"Saved {count} filtered row(s) to {path}"),
        )

    def _export_attlog(self) -> None:
        """Handle export attlog button click."""
        if not self.controller.state.processed_records:
            messagebox.showwarning("No output", "Process a file first or adjust the date filter.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".dat",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")],
        )
        if not path:
            return

        def export_sync():
            return self.controller.export_attlog(Path(path))

        self.progress_runner.run_with_progress(
            "Exporting attlog",
            export_sync,
            lambda count: self.status_panel.log(f"Exported {count} row(s) to {path}"),
        )

    def _apply_date_filter(self) -> None:
        """Handle apply date filter button click."""
        start = self.date_filter.get_start_datetime()
        end = self.date_filter.get_end_datetime()
        
        if (start is None and self.date_filter.start_date_var.get().strip()) or \
           (end is None and self.date_filter.end_date_var.get().strip()):
            messagebox.showwarning("Invalid datetime", "Invalid date/time format.")
            return

        input_count, output_count = self.controller.apply_date_filter(start, end)
        
        # Update previews
        self.input_preview.load_records(
            self.controller._get_filtered_parsed_records(),
            name_lookup=self.controller.get_employee_name,
        )
        self.output_preview.load_records(self.controller.state.processed_records)
        
        self.status_panel.log(f"Filter applied: {input_count} input row(s), {output_count} output row(s).")

    def _clear_date_filter(self) -> None:
        """Handle clear date filter button click."""
        input_count, output_count = self.controller.clear_filters()
        
        # Update previews
        self.input_preview.load_records(
            self.controller._get_filtered_parsed_records(),
            name_lookup=self.controller.get_employee_name,
        )
        self.output_preview.load_records(self.controller.state.processed_records)
        
        self.status_panel.log(f"Filter cleared: {input_count} input row(s), {output_count} output row(s).")

    def _apply_search_filter(self) -> None:
        """Handle apply search filter button click."""
        query = self.search_panel.get_search_query()
        input_count, output_count = self.controller.apply_search_filter(query)
        
        # Update previews
        self.input_preview.load_records(
            self.controller._get_filtered_parsed_records(),
            name_lookup=self.controller.get_employee_name,
        )
        self.output_preview.load_records(self.controller.state.processed_records)
        
        self.status_panel.log(
            f"Search applied for '{query}': "
            f"{input_count} input row(s), {output_count} output row(s)."
        )

    def _clear_search_filter(self) -> None:
        """Handle clear search filter button click."""
        input_count, output_count = self.controller.clear_filters()
        
        # Update previews
        self.input_preview.load_records(
            self.controller._get_filtered_parsed_records(),
            name_lookup=self.controller.get_employee_name,
        )
        self.output_preview.load_records(self.controller.state.processed_records)
        
        self.status_panel.log(f"Search cleared: {input_count} input row(s), {output_count} output row(s).")

    def _generate_dtr_pdf(self) -> None:
        """Handle generate DTR PDF button click."""
        if not self.controller.state.all_processed_records:
            messagebox.showwarning("No data", "Process attendance data first.")
            return

        # Get month from picker
        report_date = self.pdf_panel.get_selected_month()
        if not report_date:
            messagebox.showwarning("No month", "Please select a month for the DTR report.")
            return

        # Show selection dialog
        dialog = DTRSelectionDialog(self.root, self.registry)
        if dialog.result is None:
            return  # User cancelled

        # Generate PDF
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=f"DTR_{report_date.strftime('%Y_%m')}.pdf",
        )
        if not path:
            return

        def generate_sync():
            return self.controller.generate_dtr_pdf(dialog.result, report_date, Path(path))

        self.progress_runner.run_with_progress(
            "Generating DTR PDF",
            generate_sync,
            lambda result: self._on_dtr_pdf_complete(result, report_date),
        )

    def _on_dtr_pdf_complete(self, result: tuple[str, int], report_date: date) -> None:
        """Handle DTR PDF generation completion."""
        path, count = result
        self.status_panel.log(f"Generated DTR PDF for {report_date.strftime('%B %Y')}: {count} record(s) saved to {path}")

    def _open_management(self) -> None:
        """Handle manage employees button click."""
        ManagementDialog(self.root, self.registry, on_change=self._update_labels)

    def _import_user_dat(self) -> None:
        """Handle import user.dat button click."""
        path = filedialog.askopenfilename(
            title="Select user.dat",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")],
        )
        if not path:
            return

        def import_sync():
            return self.controller.import_user_dat(Path(path))

        self.progress_runner.run_with_progress(
            "Importing user.dat",
            import_sync,
            lambda result: self._on_import_user_complete(path, result),
        )

    def _on_import_user_complete(self, path: str, result: tuple[list[Any], list[Any], int]) -> None:
        """Handle user.dat import completion."""
        _employees, errors, count = result
        if errors:
            self.status_panel.log(f"user.dat import errors: {len(errors)}")
            for err in errors:
                self.status_panel.log(str(err))

        self._update_labels()
        self.status_panel.log(f"Imported {count} employee(s) from {path}")

    def _import_department_dat(self) -> None:
        """Handle import department.dat button click."""
        path = filedialog.askopenfilename(
            title="Select department.dat",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")],
        )
        if not path:
            return

        def import_sync():
            return self.controller.import_department_dat(Path(path))

        self.progress_runner.run_with_progress(
            "Importing department.dat",
            import_sync,
            lambda result: self._on_import_department_complete(path, result),
        )

    def _on_import_department_complete(self, path: str, result: tuple[list[Any], list[Any], int]) -> None:
        """Handle department.dat import completion."""
        _departments, errors, count = result
        if errors:
            self.status_panel.log(f"department.dat import errors: {len(errors)}")
            for err in errors:
                self.status_panel.log(str(err))

        self.status_panel.log(f"Imported {count} department(s) from {path}")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    initial_file = Path(args[0]) if args else None

    root = tk.Tk()
    ProcessorApp(root, initial_file=initial_file)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())