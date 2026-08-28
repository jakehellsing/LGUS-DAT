"""Input preview treeview component."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional

from lgus_dat.parser.dat_parser import ParsedRecord


class InputPreview(ttk.Treeview):
    """Treeview for displaying raw input attendance records."""

    INPUT_COLUMNS = ("Employee ID", "Employee Name", "Timestamp", "Original Record")

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, columns=self.INPUT_COLUMNS, show="headings")
        
        self._setup_columns()
        self._record_map: dict[str, ParsedRecord] = {}

    def _setup_columns(self) -> None:
        """Setup column headings and properties."""
        for col in self.INPUT_COLUMNS:
            self.heading(col, text=col)
            self.column(col, anchor="w")

    def load_records(
        self,
        records: list[ParsedRecord],
        name_lookup: Optional[dict[str, str] | Callable[[str], Optional[str]]] = None,
    ) -> int:
        """Load records into the treeview.
        
        Args:
            records: List of parsed attendance records
            name_lookup: Optional dictionary or callable function mapping employee IDs to names
            
        Returns:
            Number of records displayed
        """
        self.clear()
        self._record_map.clear()
        
        displayed = 0
        
        for rec in records:
            # Handle both dict and callable name_lookup
            if name_lookup is None:
                name = ""
            elif callable(name_lookup):
                name = name_lookup(rec.employee_id) or ""
            else:
                name = name_lookup.get(rec.employee_id, "")
            
            item = self.insert(
                "",
                tk.END,
                values=(
                    rec.employee_id,
                    name,
                    rec.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    rec.original_line,
                ),
            )
            self._record_map[item] = rec
            displayed += 1
        
        return displayed

    def clear(self) -> None:
        """Clear all records from the treeview."""
        for item in self.get_children():
            self.delete(item)
        self._record_map.clear()

    def get_selected_record(self) -> Optional[ParsedRecord]:
        """Get the currently selected record."""
        selected = self.selection()
        if not selected:
            return None
        return self._record_map.get(selected[0])

    def get_all_records(self) -> list[ParsedRecord]:
        """Get all records currently displayed."""
        return list(self._record_map.values())
