"""Dialog for editing attendance status."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from lgus_dat.domain.attendance_record import PunchStatus


class StatusEditDialog:
    """Dialog for selecting and editing attendance status."""

    def __init__(self, parent: tk.Tk, current_status: PunchStatus) -> None:
        self.parent = parent
        self.current_status = current_status
        self.result: Optional[PunchStatus] = None
        
        self._build_dialog()

    def _build_dialog(self) -> None:
        """Build the status edit dialog."""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Edit Status")
        dialog.geometry("250x120")
        dialog.transient(self.parent)
        dialog.grab_set()

        ttk.Label(dialog, text="Select status:").pack(pady=(12, 4))
        status_var = tk.StringVar(value=self.current_status.value)
        combo = ttk.Combobox(
            dialog,
            textvariable=status_var,
            values=[PunchStatus.IN.value, PunchStatus.OUT.value],
            state="readonly",
        )
        combo.pack(pady=4)

        def ok() -> None:
            try:
                self.result = PunchStatus(status_var.get())
            except ValueError:
                self.result = None
            dialog.destroy()

        def cancel() -> None:
            dialog.destroy()

        button_frame = ttk.Frame(dialog, padding=8)
        button_frame.pack()
        ttk.Button(button_frame, text="OK", command=ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=4)

        self.parent.wait_window(dialog)

    def get_result(self) -> Optional[PunchStatus]:
        """Get the selected status result."""
        return self.result
