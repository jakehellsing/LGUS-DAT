"""Progress dialog for long-running desktop operations."""

from __future__ import annotations

from typing import Any, Callable, Optional

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QProgressBar,
    QVBoxLayout,
    QLabel,
)


class WorkerThread(QThread):
    """Worker thread that runs a function and emits the result."""

    result_ready = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, func: Callable[[], Any]) -> None:
        super().__init__()
        self.func = func

    def run(self) -> None:
        try:
            result = self.func()
            self.result_ready.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(str(exc))


class ProgressDialog(QDialog):
    """Modal progress dialog with an indeterminate busy bar."""

    def __init__(
        self,
        title: str,
        message: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(300)
        self._build_ui(message)

    def _build_ui(self, message: str) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.message_label = QLabel(message)
        layout.addWidget(self.message_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)

    def closeEvent(self, event) -> None:
        """Prevent closing the dialog while the worker is running."""
        if self.worker and self.worker.isRunning():
            event.ignore()

    def run_task(self, func: Callable[[], Any]) -> Optional[Any]:
        """Run a function in a worker thread and show this dialog.

        Blocks until the worker finishes or the dialog is cancelled.
        Returns the function result, or None on error/cancellation.
        """
        self._result = None
        self._error = None

        self.worker = WorkerThread(func)
        self.worker.result_ready.connect(self._on_finished)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

        self.exec()

        if self._error:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", self._error)
            return None

        return self._result

    def _on_finished(self, result: Any) -> None:
        self._result = result
        self.accept()

    def _on_error(self, error: str) -> None:
        self._error = error
        self.reject()
