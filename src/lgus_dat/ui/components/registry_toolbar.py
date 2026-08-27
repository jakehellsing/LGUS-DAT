"""Registry operations toolbar component."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class RegistryToolbar(ttk.Frame):
    """Toolbar for employee/department registry operations."""

    def __init__(
        self,
        parent: tk.Widget,
        on_import_user: Optional[Callable[[], None]] = None,
        on_import_department: Optional[Callable[[], None]] = None,
        on_manage_employees: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent, padding=8)
        
        self.on_import_user = on_import_user
        self.on_import_department = on_import_department
        self.on_manage_employees = on_manage_employees
        
        self._build_buttons()

    def _build_buttons(self) -> None:
        """Build the toolbar buttons."""
        ttk.Button(self, text="Import user.dat", command=self._handle_import_user).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(self, text="Import department.dat", command=self._handle_import_department).pack(side=tk.LEFT, padx=4)
        ttk.Button(self, text="Manage Employees", command=self._handle_manage_employees).pack(side=tk.LEFT, padx=4)

    def _handle_import_user(self) -> None:
        """Handle import user.dat button click."""
        if self.on_import_user:
            self.on_import_user()

    def _handle_import_department(self) -> None:
        """Handle import department.dat button click."""
        if self.on_import_department:
            self.on_import_department()

    def _handle_manage_employees(self) -> None:
        """Handle manage employees button click."""
        if self.on_manage_employees:
            self.on_manage_employees()
