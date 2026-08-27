"""Output preview treeview component."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from lgus_dat.domain.attendance_record import AttendanceRecord


class OutputPreview(ttk.Treeview):
    """Treeview for displaying processed attendance records with status coloring."""

    OUTPUT_COLUMNS = ("Employee ID", "Employee Name", "Date", "Time", "Timestamp", "Status", "Exception Flag")

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, columns=self.OUTPUT_COLUMNS, show="headings")
        
        self._setup_columns()
        self._setup_tags()
        self._record_map: dict[str, AttendanceRecord] = {}

    def _setup_columns(self) -> None:
        """Setup column headings and properties."""
        for col in self.OUTPUT_COLUMNS:
            self.heading(col, text=col)
            self.column(col, anchor="w")

    def _setup_tags(self) -> None:
        """Setup color tags for status highlighting."""
        self.tag_configure("IN", background="#E3F2FD")  # Light blue
        self.tag_configure("OUT", background="#FFF9C4")  # Light yellow

    def load_records(self, records: list[AttendanceRecord]) -> int:
        """Load processed records into the treeview.
        
        Args:
            records: List of processed attendance records
            
        Returns:
            Number of records displayed
        """
        self.clear()
        self._record_map.clear()
        
        displayed = 0
        
        for rec in records:
            tag = "IN" if rec.status.value == "IN" else "OUT"
            item = self.insert(
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
                tags=(tag,),
            )
            self._record_map[item] = rec
            displayed += 1
        
        return displayed

    def clear(self) -> None:
        """Clear all records from the treeview."""
        for item in self.get_children():
            self.delete(item)
        self._record_map.clear()

    def get_selected_record(self) -> Optional[AttendanceRecord]:
        """Get the currently selected record."""
        selected = self.selection()
        if not selected:
            return None
        return self._record_map.get(selected[0])

    def get_all_records(self) -> list[AttendanceRecord]:
        """Get all records currently displayed."""
        return list(self._record_map.values())

    def update_record(self, old_record: AttendanceRecord, new_record: AttendanceRecord) -> bool:
        """Update a specific record in the treeview.
        
        Args:
            old_record: The record to be replaced
            new_record: The new record data
            
        Returns:
            True if record was found and updated, False otherwise
        """
        # Find the item containing the old record
        for item, record in self._record_map.items():
            if record == old_record:
                # Update the record in the map
                self._record_map[item] = new_record
                
                # Update the treeview values
                tag = "IN" if new_record.status.value == "IN" else "OUT"
                self.item(
                    item,
                    values=(
                        new_record.employee_id,
                        new_record.employee_name or "",
                        new_record.punch_date.isoformat(),
                        new_record.punch_time,
                        new_record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        new_record.status.value,
                        new_record.exception_flag or "",
                    ),
                    tags=(tag,),
                )
                return True
        
        return False
