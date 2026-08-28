"""Generic data table widget for record lists."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QTableView


class RecordTableModel(QAbstractTableModel):
    """Table model for a list of records and column definitions."""

    def __init__(self, columns: list[tuple[str, str]], records: list[dict[str, Any]] | None = None) -> None:
        super().__init__()
        self._columns = columns  # list of (key, header)
        self._records = records or []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._records)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            row = self._records[index.row()]
            key = self._columns[index.column()][0]
            value = row.get(key, "")
            return str(value) if value is not None else ""
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._columns[section][1]
        return None

    def set_records(self, records: list[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._records = records
        self.endResetModel()


class DataTable(QTableView):
    """Reusable table view for record data."""

    def __init__(self, columns: list[tuple[str, str]], parent=None) -> None:
        super().__init__(parent)
        self._columns = columns
        self._model = RecordTableModel(columns)
        self.setModel(self._model)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)

    def set_records(self, records: list[dict[str, Any]]) -> None:
        """Replace the displayed records."""
        self._model.set_records(records)
