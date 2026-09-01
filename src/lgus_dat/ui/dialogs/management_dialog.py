"""Employee and department management dialog for LGUS-DAT."""

from __future__ import annotations

import tkinter as tk
from dataclasses import replace
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

from lgus_dat.domain.department import Department
from lgus_dat.domain.employee import Employee
from lgus_dat.exporters.biotemplate_writer import write_biotemplate_dat
from lgus_dat.exporters.department_dat_writer import write_department_dat
from lgus_dat.exporters.user_dat_writer import write_user_dat
from lgus_dat.importers.biotemplate_parser import parse_biotemplate_dat
from lgus_dat.importers.department_parser import parse_department_dat
from lgus_dat.importers.user_parser import parse_user_dat
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

        ttk.Label(frame, text="Department:").grid(row=2, column=0, sticky=tk.W, pady=4)
        
        # Get all departments for dropdown
        departments = self.registry.all_departments()
        dept_names = [dept.name for dept in departments]
        dept_names.insert(0, "")  # Add empty option for no department
        
        # Find current department name
        current_dept_name = ""
        if employee and employee.department_id is not None:
            for dept in departments:
                if dept.department_id == employee.department_id:
                    current_dept_name = dept.name
                    break
        
        self.dept_var = tk.StringVar(value=current_dept_name)
        self.dept_combobox = ttk.Combobox(frame, textvariable=self.dept_var, values=dept_names, state="readonly")
        self.dept_combobox.grid(row=2, column=1, sticky=tk.EW, pady=4)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=12)
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side=tk.LEFT, padx=4)

        frame.columnconfigure(1, weight=1)
        self.window.wait_window(self.window)

    def _save(self) -> None:
        user_id = self.id_var.get().strip()
        name = self.name_var.get().strip()
        dept_name = self.dept_var.get().strip()

        if not user_id or not name:
            messagebox.showwarning("Validation", "User ID and Name are required.", parent=self.window)
            return

        department_id: Optional[int] = None
        if dept_name:
            # Find department ID from selected department name
            departments = self.registry.all_departments()
            for dept in departments:
                if dept.name == dept_name:
                    department_id = dept.department_id
                    break

        if not self.employee and self.registry.get_employee(user_id):
            messagebox.showwarning("Validation", f"Employee {user_id} already exists.", parent=self.window)
            return

        raw_record = self.employee.raw_record if self.employee else None
        position = self.employee.position if self.employee else None
        full_name = self.employee.full_name if self.employee else None
        self.result = Employee(
            device_user_id=user_id,
            name=name,
            full_name=full_name,
            position=position,
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


class _DepartmentDetailsDialog:
    """Dialog for viewing department details and managing employees within the department."""
    
    def __init__(
        self,
        parent: tk.Toplevel,
        registry: AttendanceRegistry,
        department: Department,
    ) -> None:
        self.registry = registry
        self.department = department
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"Department Details: {department.name}")
        self.window.geometry("600x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        self._build_ui()
        self._refresh_employees()
    
    def _build_ui(self) -> None:
        # Department info frame
        info_frame = ttk.LabelFrame(self.window, text="Department Information", padding=12)
        info_frame.pack(fill=tk.X, padx=8, pady=8)
        
        ttk.Label(info_frame, text="Department ID:").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Label(info_frame, text=str(self.department.department_id)).grid(row=0, column=1, sticky=tk.W, pady=4)
        
        ttk.Label(info_frame, text="Name:").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Label(info_frame, text=self.department.name).grid(row=1, column=1, sticky=tk.W, pady=4)
        
        # Employee count
        employee_count = len(self._get_department_employees())
        ttk.Label(info_frame, text="Employees:").grid(row=2, column=0, sticky=tk.W, pady=4)
        ttk.Label(info_frame, text=str(employee_count)).grid(row=2, column=1, sticky=tk.W, pady=4)
        
        # Employees frame
        emp_frame = ttk.LabelFrame(self.window, text="Employees in Department", padding=8)
        emp_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Employee list
        emp_cols = ("Device User ID", "Name")
        self.emp_tree = ttk.Treeview(emp_frame, columns=emp_cols, show="headings")
        for col in emp_cols:
            self.emp_tree.heading(col, text=col)
            self.emp_tree.column(col, anchor="w")
        self.emp_tree.pack(fill=tk.BOTH, expand=True)
        
        # Employee management buttons
        emp_btn_frame = ttk.Frame(emp_frame)
        emp_btn_frame.pack(fill=tk.X, pady=4)
        ttk.Button(emp_btn_frame, text="Add Employee", command=self._add_employee_to_dept).pack(side=tk.LEFT, padx=2)
        ttk.Button(emp_btn_frame, text="Remove Employee", command=self._remove_employee_from_dept).pack(side=tk.LEFT, padx=2)
        
        # Close button
        close_frame = ttk.Frame(self.window)
        close_frame.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(close_frame, text="Close", command=self.window.destroy).pack(side=tk.RIGHT, padx=2)
    
    def _get_department_employees(self) -> list[Employee]:
        """Get all employees belonging to this department."""
        all_emps = self.registry.all_employees()
        return [emp for emp in all_emps if emp.department_id == self.department.department_id]
    
    def _get_non_department_employees(self) -> list[Employee]:
        """Get all employees not belonging to this department."""
        all_emps = self.registry.all_employees()
        return [emp for emp in all_emps if emp.department_id != self.department.department_id]
    
    def _refresh_employees(self) -> None:
        """Refresh the employee list."""
        # Clear tree
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
        
        # Add employees in this department
        dept_emps = self._get_department_employees()
        for emp in dept_emps:
            self.emp_tree.insert("", tk.END, values=(emp.device_user_id, emp.name))
    
    def _add_employee_to_dept(self) -> None:
        """Add an employee to this department."""
        # Get employees not in this department
        available_emps = self._get_non_department_employees()
        if not available_emps:
            messagebox.showinfo("Info", "No available employees to add.", parent=self.window)
            return
        
        # Create selection dialog
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Employee to Department")
        dialog.geometry("400x300")
        dialog.transient(self.window)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select employee to add:").pack(pady=8)
        
        # Employee list
        emp_cols = ("Device User ID", "Name", "Current Department")
        emp_tree = ttk.Treeview(dialog, columns=emp_cols, show="headings")
        for col in emp_cols:
            emp_tree.heading(col, text=col)
            emp_tree.column(col, anchor="w")
        emp_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Get department names for display
        departments = {dept.department_id: dept.name for dept in self.registry.all_departments()}
        
        # Populate tree
        for emp in available_emps:
            current_dept = departments.get(emp.department_id, "None") if emp.department_id else "None"
            emp_tree.insert("", tk.END, values=(emp.device_user_id, emp.name, current_dept))
        
        def on_add():
            selected = emp_tree.selection()
            if not selected:
                messagebox.showwarning("Selection", "Select an employee to add.", parent=dialog)
                return
            
            values = emp_tree.item(selected[0], "values")
            user_id = str(values[0])
            employee = self.registry.get_employee(user_id)
            
            if employee:
                # Update employee's department
                updated_emp = replace(employee, department_id=self.department.department_id)
                self.registry.upsert_employee(updated_emp)
                self._refresh_employees()
                dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(btn_frame, text="Add", command=on_add).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=2)
    
    def _remove_employee_from_dept(self) -> None:
        """Remove an employee from this department."""
        selected = self.emp_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Select an employee to remove.", parent=self.window)
            return
        
        values = self.emp_tree.item(selected[0], "values")
        user_id = str(values[0])
        
        if messagebox.askyesno("Confirm", f"Remove employee {user_id} from department?", parent=self.window):
            employee = self.registry.get_employee(user_id)
            if employee:
                # Remove department assignment
                updated_emp = replace(employee, department_id=None)
                self.registry.upsert_employee(updated_emp)
                self._refresh_employees()


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

        emp_cols = ("Device User ID", "Name", "Department")
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

        dept_cols = ("Department ID", "Name", "Employee Count")
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
        ttk.Button(dept_btn_frame, text="View Details", command=self._view_department_details).pack(side=tk.LEFT, padx=2)

        # Export buttons
        export_frame = ttk.Frame(self.window)
        export_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Button(export_frame, text="Import Device Backup", command=self._import_device_backup).pack(side=tk.LEFT, padx=2)
        ttk.Button(export_frame, text="Export Device Backup", command=self._export_device_backup).pack(side=tk.LEFT, padx=2)
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
            except (ValueError, TypeError):
                return (1, str(val).lower())

        items = sorted(tree.get_children(""), key=_key, reverse=reverse)
        for index, item in enumerate(items):
            tree.move(item, "", index)
        tree.heading(col, command=lambda _col=col: self._sort_tree(tree, _col, not reverse))

    def _matches_employee_query(self, emp: Employee) -> bool:
        if not self._employee_filter_query:
            return True
        q = self._employee_filter_query.lower()
        
        # Get department name for filtering
        dept_name = ""
        if emp.department_id is not None:
            dept = self.registry.get_department(emp.department_id)
            if dept:
                dept_name = dept.name.lower()
        
        return (
            q in emp.device_user_id.lower()
            or q in emp.name.lower()
            or q in dept_name
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
        departments = {dept.department_id: dept.name for dept in self.registry.all_departments()}
        
        for emp in self.registry.all_employees():
            if self._matches_employee_query(emp):
                dept_name = departments.get(emp.department_id, "") if emp.department_id else ""
                self.emp_tree.insert(
                    "",
                    tk.END,
                    values=(emp.device_user_id, emp.name, dept_name),
                )

    def _refresh_departments(self) -> None:
        self._clear(self.dept_tree)
        
        # Get employee count for each department
        all_emps = self.registry.all_employees()
        dept_counts = {}
        for emp in all_emps:
            if emp.department_id is not None:
                dept_counts[emp.department_id] = dept_counts.get(emp.department_id, 0) + 1
        
        for dept in self.registry.all_departments():
            emp_count = dept_counts.get(dept.department_id, 0)
            self.dept_tree.insert("", tk.END, values=(dept.department_id, dept.name, emp_count))

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
            self.registry.delete_biotemplates_for_pin(user_id)
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
        
        # Check if department has employees
        dept_emps = [emp for emp in self.registry.all_employees() if emp.department_id == dept_id]
        if dept_emps:
            messagebox.showwarning(
                "Cannot Delete", 
                f"Department {dept_id} has {len(dept_emps)} employee(s). Remove employees from department first.",
                parent=self.window
            )
            return
        
        if messagebox.askyesno("Confirm", f"Delete department {dept_id}?", parent=self.window):
            self.registry.delete_department(dept_id)
            self._refresh()
            self._notify_change()

    def _view_department_details(self) -> None:
        selected = self.dept_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Select a department to view details.", parent=self.window)
            return

        values = self.dept_tree.item(selected[0], "values")
        dept_id = int(values[0])
        department = self.registry.get_department(dept_id)
        if not department:
            return

        _DepartmentDetailsDialog(self.window, self.registry, department)
        self._refresh()  # Refresh in case employees were added/removed

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

    def _import_device_backup(self) -> None:
        path = filedialog.askdirectory(title="Select device backup folder")
        if not path:
            return

        folder = Path(path)
        messages: list[str] = []

        user_dat = folder / "user.dat"
        if user_dat.exists():
            employees, errors = parse_user_dat(user_dat)
            if errors:
                messages.append(f"user.dat errors: {len(errors)}")
            count = self.registry.import_employees(employees)
            messages.append(f"user.dat: {count} employee(s)")

        dept_dat = folder / "department.dat"
        if dept_dat.exists():
            departments, errors = parse_department_dat(dept_dat)
            if errors:
                messages.append(f"department.dat errors: {len(errors)}")
            count = self.registry.import_departments(departments)
            messages.append(f"department.dat: {count} department(s)")

        bio_dat = folder / "biotemplate.dat"
        if bio_dat.exists():
            templates = parse_biotemplate_dat(bio_dat)
            count = self.registry.import_biotemplates(templates)
            messages.append(f"biotemplate.dat: {count} template(s)")

        raw_files = {}
        for fp in folder.glob("template.fp10*"):
            raw_files[fp.name] = fp.read_bytes()
        if raw_files:
            count = self.registry.import_template_files(raw_files)
            messages.append(f"template files: {count}")

        self._refresh()
        self._notify_change()
        messagebox.showinfo("Import", "\n".join(messages) or "No recognized backup files found.", parent=self.window)

    def _export_device_backup(self) -> None:
        path = filedialog.askdirectory(title="Select backup export folder")
        if not path:
            return

        folder = Path(path)
        employees = self.registry.all_employees()
        write_user_dat(employees, folder / "user.dat")

        departments = self.registry.all_departments()
        write_department_dat(departments, folder / "department.dat")

        templates = self.registry.all_biotemplates()
        write_biotemplate_dat(templates, folder / "biotemplate.dat")

        raw_files = self.registry.all_template_files()
        for filename, content in raw_files.items():
            (folder / filename).write_bytes(content)

        messagebox.showinfo(
            "Export",
            f"Exported {len(employees)} employee(s), {len(departments)} department(s), "
            f"{len(templates)} template(s) to {folder}",
            parent=self.window,
        )

    def _notify_change(self) -> None:
        if self.on_change:
            self.on_change()
