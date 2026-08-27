"""Search filter panel component."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class SearchPanel(ttk.LabelFrame):
    """Panel for employee search filtering."""

    def __init__(
        self,
        parent: tk.Widget,
        on_search: Optional[Callable[[], None]] = None,
        on_clear: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent, text="Search Filter", padding=8)
        
        self.on_search = on_search
        self.on_clear = on_clear
        
        self.search_var = tk.StringVar()
        
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the search UI components."""
        ttk.Label(self, text="Search employee:").pack(side=tk.LEFT)
        ttk.Entry(self, textvariable=self.search_var, width=24).pack(side=tk.LEFT, padx=(4, 8))
        ttk.Button(self, text="Search", command=self._handle_search).pack(side=tk.LEFT, padx=4)
        ttk.Button(self, text="Clear", command=self._handle_clear).pack(side=tk.LEFT, padx=4)

    def _handle_search(self) -> None:
        """Handle search button click."""
        if self.on_search:
            self.on_search()

    def _handle_clear(self) -> None:
        """Handle clear button click."""
        self.search_var.set("")
        if self.on_clear:
            self.on_clear()

    def get_search_query(self) -> str:
        """Get the current search query."""
        return self.search_var.get().strip()

    def has_search(self) -> bool:
        """Check if a search query is set."""
        return bool(self.search_var.get().strip())
