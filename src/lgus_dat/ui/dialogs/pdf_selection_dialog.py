"""Dialog for selecting employees/departments for DTR PDF generation."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from lgus_dat.persistence.registry import AttendanceRegistry


class DTRSelectionDialog:
    """Dialog for selecting employees and departments for DTR PDF report generation."""

    def __init__(self, parent: tk.Tk, registry: AttendanceRegistry) -> None:
        self.registry = registry
        self.result: Optional[dict] = None
        
        self.window = tk.Toplevel(parent)
        self.window.title("Select DTR Report Scope")
        self.window.geometry("500x400")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.selection_mode = tk.StringVar(value="all")
        self.selected_employees: set[str] = set()
        self.selected_departments: set[int] = set()
        
        self._build_ui()
        self._refresh_employees()
        self._refresh_departments()
        
        self.window.wait_window(self.window)

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self.window, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Selection mode
        mode_frame = ttk.LabelFrame(main_frame, text="Report Scope", padding=8)
        mode_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Radiobutton(
            mode_frame,
            text="All Employees",
            variable=self.selection_mode,
            value="all",
            command=self._on_mode_change
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(
            mode_frame,
            text="Specific Employees",
            variable=self.selection_mode,
            value="employees",
            command=self._on_mode_change
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(
            mode_frame,
            text="By Department",
            variable=self.selection_mode,
            value="departments",
            command=self._on_mode_change
        ).pack(anchor=tk.W, pady=2)
        
        # Notebook for employees and departments
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        # Employees tab
        emp_frame = ttk.Frame(self.notebook)
        self.notebook.add(emp_frame, text="Employees")
        
        emp_search_frame = ttk.Frame(emp_frame)
        emp_search_frame.pack(fill=tk.X, pady=4)
        ttk.Label(emp_search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 4))
        self.emp_search_var = tk.StringVar()
        ttk.Entry(emp_search_frame, textvariable=self.emp_search_var, width=24).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(emp_search_frame, text="Filter", command=self._filter_employees).pack(side=tk.LEFT, padx=2)
        ttk.Button(emp_search_frame, text="Clear", command=self._clear_employee_filter).pack(side=tk.LEFT, padx=2)
        
        emp_cols = ("Select", "Employee ID", "Name", "Department")
        self.emp_tree = ttk.Treeview(emp_frame, columns=emp_cols, show="headings", selectmode="extended")
        self.emp_tree.heading("Select", text="✓")
        self.emp_tree.heading("Employee ID", text="Employee ID")
        self.emp_tree.heading("Name", text="Name")
        self.emp_tree.heading("Department", text="Department")
        
        self.emp_tree.column("Select", width=40, anchor="center")
        self.emp_tree.column("Employee ID", width=100, anchor="w")
        self.emp_tree.column("Name", width=150, anchor="w")
        self.emp_tree.column("Department", width=100, anchor="w")
        
        self.emp_tree.pack(fill=tk.BOTH, expand=True)
        
        # Enable checkbox-like selection
        self.emp_tree.bind("<Button-1>", self._on_emp_click)
        
        # Departments tab
        dept_frame = ttk.Frame(self.notebook)
        self.notebook.add(dept_frame, text="Departments")
        
        dept_cols = ("Select", "Department ID", "Name")
        self.dept_tree = ttk.Treeview(dept_frame, columns=dept_cols, show="headings", selectmode="extended")
        self.dept_tree.heading("Select", text="✓")
        self.dept_tree.heading("Department ID", text="Department ID")
        self.dept_tree.heading("Name", text="Name")
        
        self.dept_tree.column("Select", width=40, anchor="center")
        self.dept_tree.column("Department ID", width=100, anchor="w")
        self.dept_tree.column("Name", width=200, anchor="w")
        
        self.dept_tree.pack(fill=tk.BOTH, expand=True)
        
        # Enable checkbox-like selection
        self.dept_tree.bind("<Button-1>", self._on_dept_click)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Generate Report", command=self._generate).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT, padx=4)
        
        self._employee_filter_query = ""

    def _on_mode_change(self) -> None:
        mode = self.selection_mode.get()
        if mode == "all":
            self.notebook.config(state="disabled")
        elif mode == "employees":
            self.notebook.config(state="normal")
            self.notebook.select(0)  # Select employees tab
        elif mode == "departments":
            self.notebook.config(state="normal")
            self.notebook.select(1)  # Select departments tab

    def _on_emp_click(self, event) -> None:
        region = self.emp_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.emp_tree.identify_column(event.x)
            if column == "#1":  # Select column
                item = self.emp_tree.identify_row(event.y)
                if item:
                    values = self.emp_tree.item(item, "values")
                    emp_id = values[1]
                    if emp_id in self.selected_employees:
                        self.selected_employees.remove(emp_id)
                        self.emp_tree.item(item, values=("", *values[1:]))
                    else:
                        self.selected_employees.add(emp_id)
                        self.emp_tree.item(item, values=("✓", *values[1:]))

    def _on_dept_click(self, event) -> None:
        region = self.dept_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.dept_tree.identify_column(event.x)
            if column == "#1":  # Select column
                item = self.dept_tree.identify_row(event.y)
                if item:
                    values = self.dept_tree.item(item, "values")
                    dept_id = int(values[1])
                    if dept_id in self.selected_departments:
                        self.selected_departments.remove(dept_id)
                        self.dept_tree.item(item, values=("", *values[1:]))
                    else:
                        self.selected_departments.add(dept_id)
                        self.dept_tree.item(item, values=("✓", *values[1:]))

    def _refresh_employees(self) -> None:
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
        
        for emp in self.registry.all_employees():
            if self._matches_employee_query(emp):
                check = "✓" if emp.device_user_id in self.selected_employees else ""
                dept_name = ""
                if emp.department_id is not None:
                    dept = self.registry.get_department(emp.department_id)
                    if dept:
                        dept_name = dept.name
                
                self.emp_tree.insert(
                    "",
                    tk.END,
                    values=(check, emp.device_user_id, emp.name, dept_name),
                )

    def _refresh_departments(self) -> None:
        for item in self.dept_tree.get_children():
            self.dept_tree.delete(item)
        
        for dept in self.registry.all_departments():
            check = "✓" if dept.department_id in self.selected_departments else ""
            self.dept_tree.insert(
                "",
                tk.END,
                values=(check, str(dept.department_id), dept.name),
            )

    def _matches_employee_query(self, emp) -> bool:
        if not self._employee_filter_query:
            return True
        q = self._employee_filter_query.lower()
        return (
            q in emp.device_user_id.lower()
            or q in emp.name.lower()
            or (emp.department_id is not None and q in str(emp.department_id).lower())
        )

    def _filter_employees(self) -> None:
        self._employee_filter_query = self.emp_search_var.get()
        self._refresh_employees()

    def _clear_employee_filter(self) -> None:
        self.emp_search_var.set("")
        self._employee_filter_query = ""
        self._refresh_employees()

    def _generate(self) -> None:
        mode = self.selection_mode.get()
        
        if mode == "all":
            self.result = {"mode": "all"}
        elif mode == "employees":
            if not self.selected_employees:
                self._show_warning("No Selection", "Please select at least one employee.")
                return
            self.result = {"mode": "employees", "employee_ids": list(self.selected_employees)}
        elif mode == "departments":
            if not self.selected_departments:
                self._show_warning("No Selection", "Please select at least one department.")
                return
            self.result = {"mode": "departments", "department_ids": list(self.selected_departments)}

    def _show_warning(self, title: str, message: str) -> None:
        """Show a warning message box."""
        from tkinter import messagebox
        messagebox.showwarning(title, message, parent=self.window)
        
        self.window.destroy()