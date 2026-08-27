"""File operations toolbar component."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class FileToolbar(ttk.Frame):
    """Toolbar for file operations: open, process, save, export."""

    def __init__(
        self,
        parent: tk.Widget,
        on_open: Optional[Callable[[], None]] = None,
        on_process: Optional[Callable[[], None]] = None,
        on_process_from_db: Optional[Callable[[], None]] = None,
        on_save_csv: Optional[Callable[[], None]] = None,
        on_export_attlog: Optional[Callable[[], None]] = None,
        on_edit_status: Optional[Callable[[], None]] = None,
        on_f5_process: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent, padding=8)
        
        self.on_open = on_open
        self.on_process = on_process
        self.on_process_from_db = on_process_from_db
        self.on_save_csv = on_save_csv
        self.on_export_attlog = on_export_attlog
        self.on_edit_status = on_edit_status
        self.on_f5_process = on_f5_process
        
        self._build_buttons()

    def _build_buttons(self) -> None:
        """Build the toolbar buttons."""
        ttk.Button(self, text="Open .DAT", command=self._handle_open).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(self, text="Process (F5)", command=self._handle_process).pack(side=tk.LEFT, padx=4)
        ttk.Button(self, text="Process from DB", command=self._handle_process_from_db).pack(side=tk.LEFT, padx=4)
        ttk.Button(self, text="Save CSV", command=self._handle_save_csv).pack(side=tk.LEFT, padx=4)
        ttk.Button(self, text="Export attlog.dat", command=self._handle_export_attlog).pack(side=tk.LEFT, padx=4)
        ttk.Button(self, text="Edit Status", command=self._handle_edit_status).pack(side=tk.LEFT, padx=4)

    def _handle_open(self) -> None:
        """Handle open button click."""
        if self.on_open:
            self.on_open()

    def _handle_process(self) -> None:
        """Handle process button click."""
        if self.on_process:
            self.on_process()

    def _handle_process_from_db(self) -> None:
        """Handle process from DB button click."""
        if self.on_process_from_db:
            self.on_process_from_db()

    def _handle_save_csv(self) -> None:
        """Handle save CSV button click."""
        if self.on_save_csv:
            self.on_save_csv()

    def _handle_export_attlog(self) -> None:
        """Handle export attlog button click."""
        if self.on_export_attlog:
            self.on_export_attlog()

    def _handle_edit_status(self) -> None:
        """Handle edit status button click."""
        if self.on_edit_status:
            self.on_edit_status()

    def bind_f5(self, root: tk.Tk) -> None:
        """Bind F5 key to process function."""
        if self.on_f5_process:
            root.bind("<F5>", lambda _event: self.on_f5_process())
