"""Tkinter desktop application for processing MB10-VL .DAT files."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from lgus_dat.domain.attendance_record import AttendanceRecord
from lgus_dat.importers.department_parser import parse_department_dat
from lgus_dat.importers.user_parser import parse_user_dat
from lgus_dat.output.csv_writer import write_csv
from lgus_dat.parser.dat_parser import parse_dat_file
from lgus_dat.persistence.registry import AttendanceRegistry
from lgus_dat.processing.sequence_processor import process_records
from lgus_dat.ui.management_dialog import ManagementDialog


class ProcessorApp:
    def __init__(self, root: tk.Tk, initial_file: Optional[Path] = None) -> None:
        self.root = root
        self.root.title("LGUS-DAT — MB10-VL Attendance Processor")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)

        self.current_input_path: Optional[Path] = None
        self.parsed_records: list = []
        self.processed_records: list[AttendanceRecord] = []
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

        self.root.bind("<F5>", lambda _event: self._process())

        registry_toolbar = ttk.Frame(self.root, padding=8)
        registry_toolbar.pack(fill=tk.X)

        ttk.Button(registry_toolbar, text="Import user.dat", command=self._import_user_dat).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(registry_toolbar, text="Import department.dat", command=self._import_department_dat).pack(side=tk.LEFT, padx=4)
        ttk.Button(registry_toolbar, text="Manage Employees", command=self._open_management).pack(side=tk.LEFT, padx=4)

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
        self.processed_records = []
        self._log(f"Opened {self.current_input_path}")

        records, errors = parse_dat_file(self.current_input_path)
        self.parsed_records = records

        for rec in records:
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

        if errors:
            self._log(f"Found {len(errors)} parse error(s):")
            for err in errors:
                self._log(str(err))
        else:
            self._log(f"Parsed {len(records)} record(s) successfully.")

    def _process(self) -> None:
        if not self.parsed_records:
            messagebox.showwarning("No data", "Open a .DAT file first.")
            return

        self._clear(self.output_tree)
        self.processed_records = process_records(
            self.parsed_records,
            name_lookup=self.registry.employee_name,
        )

        for rec in self.processed_records:
            self.output_tree.insert(
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

        self._log(f"Processed {len(self.processed_records)} record(s).")

    def _save_csv(self) -> None:
        if not self.processed_records:
            messagebox.showwarning("No output", "Process a file first.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        write_csv(self.processed_records, Path(path))
        self._log(f"Saved CSV to {path}")

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
