"""Tkinter desktop application for processing MB10-VL .DAT files."""

from __future__ import annotations

import sys
import tkinter as tk
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from tkcalendar import DateEntry

from lgus_dat.domain.attendance_record import AttendanceRecord, PunchStatus
from lgus_dat.importers.department_parser import parse_department_dat
from lgus_dat.importers.user_parser import parse_user_dat
from lgus_dat.output.attlog_writer import write_attlog
from lgus_dat.output.csv_writer import write_csv
from lgus_dat.parser.dat_parser import ParsedRecord, parse_dat_file
from lgus_dat.persistence.registry import AttendanceRegistry
from lgus_dat.processing.sequence_processor import process_records
from lgus_dat.ui.date_filter import filter_by_date
from lgus_dat.ui.management_dialog import ManagementDialog
from lgus_dat.ui.search_filter import filter_by_search


class ProcessorApp:
    def __init__(self, root: tk.Tk, initial_file: Optional[Path] = None) -> None:
        self.root = root
        self.root.title("LGUS-DAT — MB10-VL Attendance Processor")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)

        self.current_input_path: Optional[Path] = None
        self.parsed_records: list[ParsedRecord] = []
        self.all_processed_records: list[AttendanceRecord] = []
        self.processed_records: list[AttendanceRecord] = []
        self._filter_start: Optional[date] = None
        self._filter_end: Optional[date] = None
        self._search_query: str = ""
        self._output_tree_records: dict[str, AttendanceRecord] = {}
        self.registry = AttendanceRegistry()

        self._build_ui()
        self._update_registry_label()

        if initial_file:
            self._load_file(initial_file)

    def _build_ui(self) -> None:
        # Toolbar
        toolbar = ttk.Frame(self.root, padding=8)
        toolbar.pack(fill=tk.X)

        ttk.Button(toolbar, text="Open .DAT", command=self._open_file).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(toolbar, text="Process (F5)", command=self._process).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Save CSV", command=self._save_csv).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Export attlog.dat", command=self._export_attlog).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Edit Status", command=self._edit_selected_status).pack(side=tk.LEFT, padx=4)

        self.root.bind("<F5>", lambda _event: self._process())

        registry_toolbar = ttk.Frame(self.root, padding=8)
        registry_toolbar.pack(fill=tk.X)

        ttk.Button(registry_toolbar, text="Import user.dat", command=self._import_user_dat).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(registry_toolbar, text="Import department.dat", command=self._import_department_dat).pack(side=tk.LEFT, padx=4)
        ttk.Button(registry_toolbar, text="Manage Employees", command=self._open_management).pack(side=tk.LEFT, padx=4)

        # Date range filter toolbar
        filter_toolbar = ttk.LabelFrame(self.root, text="Date Range Filter", padding=8)
        filter_toolbar.pack(fill=tk.X, padx=8, pady=(0, 4))

        ttk.Label(filter_toolbar, text="Start:").pack(side=tk.LEFT)
        self.start_date_var = tk.StringVar()
        self.start_date_entry = DateEntry(
            filter_toolbar,
            textvariable=self.start_date_var,
            width=12,
            date_pattern="y-mm-dd",
        )
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.pack(side=tk.LEFT, padx=(4, 8))

        ttk.Label(filter_toolbar, text="End:").pack(side=tk.LEFT)
        self.end_date_var = tk.StringVar()
        self.end_date_entry = DateEntry(
            filter_toolbar,
            textvariable=self.end_date_var,
            width=12,
            date_pattern="y-mm-dd",
        )
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.pack(side=tk.LEFT, padx=(4, 8))

        ttk.Button(filter_toolbar, text="Apply Filter", command=self._apply_date_filter).pack(side=tk.LEFT, padx=4)
        ttk.Button(filter_toolbar, text="Clear", command=self._clear_date_filter).pack(side=tk.LEFT, padx=4)

        # Search filter toolbar
        search_toolbar = ttk.LabelFrame(self.root, text="Search Filter", padding=8)
        search_toolbar.pack(fill=tk.X, padx=8, pady=(0, 4))

        ttk.Label(search_toolbar, text="Search employee:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        ttk.Entry(search_toolbar, textvariable=self.search_var, width=24).pack(side=tk.LEFT, padx=(4, 8))
        ttk.Button(search_toolbar, text="Search", command=self._apply_search_filter).pack(side=tk.LEFT, padx=4)
        ttk.Button(search_toolbar, text="Clear", command=self._clear_search_filter).pack(side=tk.LEFT, padx=4)

        # File path label
        self.path_label = ttk.Label(self.root, text="No file selected", padding=8)
        self.path_label.pack(fill=tk.X)

        self.registry_label = ttk.Label(
            self.root,
            text=f"Registry: {self.registry.db_path} — 0 employees",
            padding=8,
        )
        self.registry_label.pack(fill=tk.X)

        # Notebook with input preview and output
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # Input preview tab
        input_frame = ttk.Frame(notebook)
        notebook.add(input_frame, text="Input Preview")

        input_columns = ("Employee ID", "Employee Name", "Timestamp", "Original Record")
        self.input_tree = ttk.Treeview(input_frame, columns=input_columns, show="headings")
        for col in input_columns:
            self.input_tree.heading(col, text=col)
            self.input_tree.column(col, anchor="w")
        self.input_tree.pack(fill=tk.BOTH, expand=True)

        # Output tab
        output_frame = ttk.Frame(notebook)
        notebook.add(output_frame, text="Processed Output")

        output_columns = ("Employee ID", "Employee Name", "Date", "Time", "Timestamp", "Status", "Exception Flag")
        self.output_tree = ttk.Treeview(output_frame, columns=output_columns, show="headings")
        for col in output_columns:
            self.output_tree.heading(col, text=col)
            self.output_tree.column(col, anchor="w")
        self.output_tree.pack(fill=tk.BOTH, expand=True)

        # Status / errors
        status_frame = ttk.LabelFrame(self.root, text="Status / Errors", padding=8)
        status_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        self.status_text = tk.Text(status_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        self.status_text.pack(fill=tk.BOTH, expand=True)

    def _log(self, message: str) -> None:
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)

    def _clear(self, tree: ttk.Treeview) -> None:
        for item in tree.get_children():
            tree.delete(item)

    def _update_registry_label(self) -> None:
        with self.registry._connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        self.registry_label.config(text=f"Registry: {self.registry.db_path} — {count} employees")

    def _parse_date_var(self, var: tk.StringVar) -> Optional[date]:
        text = var.get().strip()
        if not text:
            return None
        try:
            return date.fromisoformat(text)
        except ValueError:
            messagebox.showwarning("Invalid date", f"'{text}' is not a valid YYYY-MM-DD date.")
            return None

    def _refresh_filter_dates(self) -> bool:
        start = self._parse_date_var(self.start_date_var)
        if start is None and self.start_date_var.get().strip():
            return False
        end = self._parse_date_var(self.end_date_var)
        if end is None and self.end_date_var.get().strip():
            return False
        self._filter_start, self._filter_end = start, end
        return True

    def _filtered_parsed_records(self) -> list[ParsedRecord]:
        records = filter_by_date(
            self.parsed_records,
            lambda rec: rec.timestamp.date(),
            self._filter_start,
            self._filter_end,
        )
        return filter_by_search(
            records,
            self._search_query,
            [
                lambda rec: rec.employee_id,
                lambda rec: self.registry.employee_name(rec.employee_id) or "",
            ],
        )

    def _filtered_processed_records(self) -> list[AttendanceRecord]:
        records = filter_by_date(
            self.all_processed_records,
            lambda rec: rec.punch_date,
            self._filter_start,
            self._filter_end,
        )
        return filter_by_search(
            records,
            self._search_query,
            [
                lambda rec: rec.employee_id,
                lambda rec: rec.employee_name or "",
            ],
        )

    def _refresh_input_tree(self) -> int:
        self._clear(self.input_tree)
        displayed = 0
        for rec in self._filtered_parsed_records():
            name = self.registry.employee_name(rec.employee_id) or ""
            self.input_tree.insert(
                "",
                tk.END,
                values=(
                    rec.employee_id,
                    name,
                    rec.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    rec.original_line,
                ),
            )
            displayed += 1
        return displayed

    def _refresh_output_tree(self) -> int:
        self._clear(self.output_tree)
        self._output_tree_records.clear()
        self.processed_records = self._filtered_processed_records()
        for rec in self.processed_records:
            item = self.output_tree.insert(
                "",
                tk.END,
                values=(
                    rec.employee_id,
                    rec.employee_name or "",
                    rec.punch_date.isoformat(),
                    rec.punch_time,
                    rec.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    rec.status.value,
                    rec.exception_flag or "",
                ),
            )
            self._output_tree_records[item] = rec
        return len(self.processed_records)

    def _apply_date_filter(self) -> None:
        if not self._refresh_filter_dates():
            return
        displayed_input = self._refresh_input_tree()
        displayed_output = self._refresh_output_tree()
        self._log(f"Filter applied: {displayed_input} input row(s), {displayed_output} output row(s).")

    def _clear_date_filter(self) -> None:
        self.start_date_var.set("")
        self.end_date_var.set("")
        self._filter_start = None
        self._filter_end = None
        self._apply_date_filter()

    def _apply_search_filter(self) -> None:
        self._search_query = self.search_var.get()
        displayed_input = self._refresh_input_tree()
        displayed_output = self._refresh_output_tree()
        self._log(
            f"Search applied for '{self._search_query}': "
            f"{displayed_input} input row(s), {displayed_output} output row(s)."
        )

    def _clear_search_filter(self) -> None:
        self.search_var.set("")
        self._search_query = ""
        self._apply_search_filter()

    def _open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select MB10-VL .DAT export",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")],
        )
        if path:
            self._load_file(Path(path))

    def _load_file(self, path: Path) -> None:
        self.current_input_path = path
        self.path_label.config(text=str(self.current_input_path))
        self._clear(self.input_tree)
        self._clear(self.output_tree)
        self.all_processed_records = []
        self.processed_records = []
        self._log(f"Opened {self.current_input_path}")

        records, errors = parse_dat_file(self.current_input_path)
        self.parsed_records = records

        displayed = self._refresh_input_tree()

        if errors:
            self._log(f"Found {len(errors)} parse error(s):")
            for err in errors:
                self._log(str(err))
        else:
            self._log(f"Parsed {len(records)} record(s) successfully. {displayed} shown with current filter.")

    def _process(self) -> None:
        if not self.parsed_records:
            messagebox.showwarning("No data", "Open a .DAT file first.")
            return

        self.all_processed_records = process_records(
            self.parsed_records,
            name_lookup=self.registry.employee_name,
        )

        displayed = self._refresh_output_tree()
        self._log(f"Processed {len(self.all_processed_records)} record(s). {displayed} shown with current filter.")

    def _edit_status_dialog(self, current: PunchStatus) -> Optional[PunchStatus]:
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Status")
        dialog.geometry("250x120")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Select status:").pack(pady=(12, 4))
        status_var = tk.StringVar(value=current.value)
        combo = ttk.Combobox(
            dialog,
            textvariable=status_var,
            values=[PunchStatus.IN.value, PunchStatus.OUT.value],
            state="readonly",
        )
        combo.pack(pady=4)

        result: Optional[PunchStatus] = None

        def ok() -> None:
            nonlocal result
            try:
                result = PunchStatus(status_var.get())
            except ValueError:
                result = None
            dialog.destroy()

        def cancel() -> None:
            dialog.destroy()

        button_frame = ttk.Frame(dialog, padding=8)
        button_frame.pack()
        ttk.Button(button_frame, text="OK", command=ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=4)

        self.root.wait_window(dialog)
        return result

    def _edit_selected_status(self) -> None:
        selected = self.output_tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select a processed output row to edit its status.")
            return

        item = selected[0]
        record = self._output_tree_records.get(item)
        if record is None:
            return

        new_status = self._edit_status_dialog(record.status)
        if new_status is None or new_status == record.status:
            return

        edited = replace(record, status=new_status, exception_flag="MANUAL_EDIT")
        try:
            index = self.all_processed_records.index(record)
            self.all_processed_records[index] = edited
        except ValueError:
            self._log(f"Could not update {record.employee_id} — original row not found.")
            return

        self._refresh_output_tree()
        self._log(
            f"Manual edit: {record.employee_id} at "
            f"{record.timestamp.strftime('%Y-%m-%d %H:%M:%S')} changed from "
            f"{record.status.value} to {edited.status.value}"
        )

    def _save_csv(self) -> None:
        if not self.processed_records:
            messagebox.showwarning("No output", "Process a file first or adjust the date filter.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        write_csv(self.processed_records, Path(path))
        self._log(f"Saved {len(self.processed_records)} filtered row(s) to {path}")

    def _export_attlog(self) -> None:
        if not self.processed_records:
            messagebox.showwarning("No output", "Process a file first or adjust the date filter.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".dat",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")],
        )
        if not path:
            return

        write_attlog(self.processed_records, Path(path))
        self._log(f"Exported {len(self.processed_records)} row(s) to {path}")

    def _open_management(self) -> None:
        ManagementDialog(self.root, self.registry, on_change=self._update_registry_label)

    def _import_user_dat(self) -> None:
        path = filedialog.askopenfilename(
            title="Select user.dat",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")],
        )
        if not path:
            return

        employees, errors = parse_user_dat(Path(path))
        if errors:
            self._log(f"user.dat import errors: {len(errors)}")
            for err in errors:
                self._log(str(err))

        count = self.registry.import_employees(employees)
        self._update_registry_label()
        self._log(f"Imported {count} employee(s) from {path}")

    def _import_department_dat(self) -> None:
        path = filedialog.askopenfilename(
            title="Select department.dat",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")],
        )
        if not path:
            return

        departments, errors = parse_department_dat(Path(path))
        if errors:
            self._log(f"department.dat import errors: {len(errors)}")
            for err in errors:
                self._log(str(err))

        count = self.registry.import_departments(departments)
        self._log(f"Imported {count} department(s) from {path}")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    initial_file = Path(args[0]) if args else None

    root = tk.Tk()
    ProcessorApp(root, initial_file=initial_file)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
