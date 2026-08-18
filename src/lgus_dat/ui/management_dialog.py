"""Employee and department management dialog for LGUS-DAT."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

from lgus_dat.domain.department import Department
from lgus_dat.domain.employee import Employee
from lgus_dat.exporters.department_dat_writer import write_department_dat
from lgus_dat.exporters.user_dat_writer import write_user_dat
from lgus_dat.persistence.registry import AttendanceRegistry


class _EmployeeDialog:
    def __init__(
        self,
        parent: tk.Toplevel,
        registry: AttendanceRegistry,
        employee: Optional[Employee] = None,
    ) -> None:
        self.registry = registry
        self.employee = employee
        self.result: Optional[Employee] = None

        self.window = tk.Toplevel(parent)
        self.window.title("Edit Employee" if employee else "Add Employee")
        self.window.transient(parent)
        self.window.grab_set()

        frame = ttk.Frame(self.window, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Device User ID:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.id_var = tk.StringVar(value=employee.device_user_id if employee else "")
        self.id_entry = ttk.Entry(frame, textvariable=self.id_var, state="readonly" if employee else "normal")
        self.id_entry.grid(row=0, column=1, sticky=tk.EW, pady=4)

        ttk.Label(frame, text="Name:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.name_var = tk.StringVar(value=employee.name if employee else "")
        ttk.Entry(frame, textvariable=self.name_var).grid(row=1, column=1, sticky=tk.EW, pady=4)

        ttk.Label(frame, text="Department ID:").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.dept_var = tk.StringVar(
            value=str(employee.department_id) if employee and employee.department_id is not None else ""
        )
        ttk.Entry(frame, textvariable=self.dept_var).grid(row=2, column=1, sticky=tk.EW, pady=4)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=12)
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side=tk.LEFT, padx=4)

        frame.columnconfigure(1, weight=1)
        self.window.wait_window(self.window)

    def _save(self) -> None:
        user_id = self.id_var.get().strip()
        name = self.name_var.get().strip()
        dept_text = self.dept_var.get().strip()

        if not user_id or not name:
            messagebox.showwarning("Validation", "User ID and Name are required.", parent=self.window)
            return

        department_id: Optional[int] = None
        if dept_text:
            try:
                department_id = int(dept_text)
            except ValueError:
                messagebox.showwarning("Validation", "Department ID must be a number.", parent=self.window)
                return

        if not self.employee and self.registry.get_employee(user_id):
            messagebox.showwarning("Validation", f"Employee {user_id} already exists.", parent=self.window)
            return

        raw_record = self.employee.raw_record if self.employee else None
        self.result = Employee(
            device_user_id=user_id,
            name=name,
            department_id=department_id,
            raw_record=raw_record,
        )
        self.window.destroy()


class _DepartmentDialog:
    def __init__(
        self,
        parent: tk.Toplevel,
        registry: AttendanceRegistry,
        department: Optional[Department] = None,
    ) -> None:
        self.registry = registry
        self.department = department
        self.result: Optional[Department] = None

        self.window = tk.Toplevel(parent)
        self.window.title("Edit Department" if department else "Add Department")
        self.window.transient(parent)
        self.window.grab_set()

        frame = ttk.Frame(self.window, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Department ID:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.id_var = tk.StringVar(value=str(department.department_id) if department else "")
        self.id_entry = ttk.Entry(frame, textvariable=self.id_var, state="readonly" if department else "normal")
        self.id_entry.grid(row=0, column=1, sticky=tk.EW, pady=4)

        ttk.Label(frame, text="Name:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.name_var = tk.StringVar(value=department.name if department else "")
        ttk.Entry(frame, textvariable=self.name_var).grid(row=1, column=1, sticky=tk.EW, pady=4)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=12)
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side=tk.LEFT, padx=4)

        frame.columnconfigure(1, weight=1)
        self.window.wait_window(self.window)

    def _save(self) -> None:
        dept_id_text = self.id_var.get().strip()
        name = self.name_var.get().strip()

        if not dept_id_text or not name:
            messagebox.showwarning("Validation", "Department ID and Name are required.", parent=self.window)
            return

        try:
            department_id = int(dept_id_text)
        except ValueError:
            messagebox.showwarning("Validation", "Department ID must be a number.", parent=self.window)
            return

        if not self.department and self.registry.get_department(department_id):
            messagebox.showwarning("Validation", f"Department {department_id} already exists.", parent=self.window)
            return

        raw_record = self.department.raw_record if self.department else None
        self.result = Department(department_id=department_id, name=name, raw_record=raw_record)
        self.window.destroy()


class ManagementDialog:
    """Top-level management window for employees and departments."""

    def __init__(
        self,
        parent: tk.Tk,
        registry: AttendanceRegistry,
        on_change: Optional[Callable[[], None]] = None,
    ) -> None:
        self.registry = registry
        self.on_change = on_change

        self.window = tk.Toplevel(parent)
        self.window.title("Employee & Department Management")
        self.window.geometry("700x500")
        self.window.minsize(600, 400)
        self.window.transient(parent)

        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Employees tab
        emp_frame = ttk.Frame(notebook)
        notebook.add(emp_frame, text="Employees")

        emp_search_frame = ttk.Frame(emp_frame)
        emp_search_frame.pack(fill=tk.X, pady=4)
        ttk.Label(emp_search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 4))
        self.emp_search_var = tk.StringVar()
        ttk.Entry(emp_search_frame, textvariable=self.emp_search_var, width=24).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(emp_search_frame, text="Filter", command=self._filter_employees).pack(side=tk.LEFT, padx=2)
        ttk.Button(emp_search_frame, text="Clear", command=self._clear_employee_filter).pack(side=tk.LEFT, padx=2)

        emp_cols = ("Device User ID", "Name", "Department ID")
        self.emp_tree = ttk.Treeview(emp_frame, columns=emp_cols, show="headings")
        for col in emp_cols:
            self.emp_tree.heading(col, text=col, command=lambda _col=col: self._sort_tree(self.emp_tree, _col))
            self.emp_tree.column(col, anchor="w")
        self.emp_tree.pack(fill=tk.BOTH, expand=True)

        emp_btn_frame = ttk.Frame(emp_frame)
        emp_btn_frame.pack(fill=tk.X, pady=4)
        ttk.Button(emp_btn_frame, text="Add", command=self._add_employee).pack(side=tk.LEFT, padx=2)
        ttk.Button(emp_btn_frame, text="Edit", command=self._edit_employee).pack(side=tk.LEFT, padx=2)
        ttk.Button(emp_btn_frame, text="Delete", command=self._delete_employee).pack(side=tk.LEFT, padx=2)

        self._employee_filter_query = ""

        # Departments tab
        dept_frame = ttk.Frame(notebook)
        notebook.add(dept_frame, text="Departments")

        dept_cols = ("Department ID", "Name")
        self.dept_tree = ttk.Treeview(dept_frame, columns=dept_cols, show="headings")
        for col in dept_cols:
            self.dept_tree.heading(col, text=col, command=lambda _col=col: self._sort_tree(self.dept_tree, _col))
            self.dept_tree.column(col, anchor="w")
        self.dept_tree.pack(fill=tk.BOTH, expand=True)

        dept_btn_frame = ttk.Frame(dept_frame)
        dept_btn_frame.pack(fill=tk.X, pady=4)
        ttk.Button(dept_btn_frame, text="Add", command=self._add_department).pack(side=tk.LEFT, padx=2)
        ttk.Button(dept_btn_frame, text="Edit", command=self._edit_department).pack(side=tk.LEFT, padx=2)
        ttk.Button(dept_btn_frame, text="Delete", command=self._delete_department).pack(side=tk.LEFT, padx=2)

        # Export buttons
        export_frame = ttk.Frame(self.window)
        export_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Button(export_frame, text="Export user.dat", command=self._export_user_dat).pack(side=tk.LEFT, padx=2)
        ttk.Button(export_frame, text="Export department.dat", command=self._export_department_dat).pack(
            side=tk.LEFT, padx=2
        )

    def _clear(self, tree: ttk.Treeview) -> None:
        for item in tree.get_children():
            tree.delete(item)

    def _sort_tree(self, tree: ttk.Treeview, col: str, reverse: bool = False) -> None:
        def _key(item: str):
            val = tree.set(item, col)
            try:
                return (0, float(val))
            except ValueError:
                return (1, val.lower())

        items = sorted(tree.get_children(""), key=_key, reverse=reverse)
        for index, item in enumerate(items):
            tree.move(item, "", index)
        tree.heading(col, command=lambda _col=col: self._sort_tree(tree, _col, not reverse))

    def _matches_employee_query(self, emp: Employee) -> bool:
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

    def _refresh_employees(self) -> None:
        self._clear(self.emp_tree)
        for emp in self.registry.all_employees():
            if self._matches_employee_query(emp):
                self.emp_tree.insert(
                    "",
                    tk.END,
                    values=(emp.device_user_id, emp.name, emp.department_id or ""),
                )

    def _refresh_departments(self) -> None:
        self._clear(self.dept_tree)
        for dept in self.registry.all_departments():
            self.dept_tree.insert("", tk.END, values=(dept.department_id, dept.name))

    def _refresh(self) -> None:
        self._refresh_employees()
        self._refresh_departments()

    def _add_employee(self) -> None:
        dialog = _EmployeeDialog(self.window, self.registry)
        if dialog.result:
            self.registry.upsert_employee(dialog.result)
            self._refresh()
            self._notify_change()

    def _edit_employee(self) -> None:
        selected = self.emp_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Select an employee to edit.", parent=self.window)
            return

        values = self.emp_tree.item(selected[0], "values")
        employee = self.registry.get_employee(str(values[0]))
        if not employee:
            return

        dialog = _EmployeeDialog(self.window, self.registry, employee)
        if dialog.result:
            self.registry.upsert_employee(dialog.result)
            self._refresh()
            self._notify_change()

    def _delete_employee(self) -> None:
        selected = self.emp_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Select an employee to delete.", parent=self.window)
            return

        values = self.emp_tree.item(selected[0], "values")
        user_id = str(values[0])
        if messagebox.askyesno("Confirm", f"Delete employee {user_id}?", parent=self.window):
            self.registry.delete_employee(user_id)
            self._refresh()
            self._notify_change()

    def _add_department(self) -> None:
        dialog = _DepartmentDialog(self.window, self.registry)
        if dialog.result:
            self.registry.upsert_department(dialog.result)
            self._refresh()
            self._notify_change()

    def _edit_department(self) -> None:
        selected = self.dept_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Select a department to edit.", parent=self.window)
            return

        values = self.dept_tree.item(selected[0], "values")
        department = self.registry.get_department(int(values[0]))
        if not department:
            return

        dialog = _DepartmentDialog(self.window, self.registry, department)
        if dialog.result:
            self.registry.upsert_department(dialog.result)
            self._refresh()
            self._notify_change()

    def _delete_department(self) -> None:
        selected = self.dept_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Select a department to delete.", parent=self.window)
            return

        values = self.dept_tree.item(selected[0], "values")
        dept_id = int(values[0])
        if messagebox.askyesno("Confirm", f"Delete department {dept_id}?", parent=self.window):
            self.registry.delete_department(dept_id)
            self._refresh()
            self._notify_change()

    def _export_user_dat(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".dat",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")],
        )
        if not path:
            return
        employees = self.registry.all_employees()
        write_user_dat(employees, Path(path))
        messagebox.showinfo("Export", f"Exported {len(employees)} employee(s) to {path}", parent=self.window)

    def _export_department_dat(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".dat",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")],
        )
        if not path:
            return
        departments = self.registry.all_departments()
        write_department_dat(departments, Path(path))
        messagebox.showinfo(
            "Export", f"Exported {len(departments)} department(s) to {path}", parent=self.window
        )

    def _notify_change(self) -> None:
        if self.on_change:
            self.on_change()
