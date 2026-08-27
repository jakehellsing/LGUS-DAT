"""Status panel component for displaying messages and errors."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class StatusPanel(ttk.LabelFrame):
    """Panel for displaying status messages and errors."""

    def __init__(self, parent: tk.Widget, height: int = 6) -> None:
        super().__init__(parent, text="Status / Errors", padding=8)
        
        self.status_text = tk.Text(self, height=height, wrap=tk.WORD, state=tk.DISABLED)
        self.status_text.pack(fill=tk.BOTH, expand=True)

    def log(self, message: str) -> None:
        """Add a message to the status panel.
        
        Args:
            message: The message to log
        """
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)

    def clear(self) -> None:
        """Clear all messages from the status panel."""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)

    def get_text(self) -> str:
        """Get the current text content of the status panel."""
        return self.status_text.get(1.0, tk.END).strip()
