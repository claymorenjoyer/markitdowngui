"""Background conversion worker so the UI never blocks."""

from __future__ import annotations

from typing import List

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from converter import (
    ConversionItem,
    ConverterOptions,
    build_markitdown,
    convert_item,
)


class WorkerSignals(QObject):
    # index in the batch, the (mutated) item
    item_done = Signal(int, object)
    # number completed, total
    progress = Signal(int, int)
    finished = Signal()


class ConversionWorker(QRunnable):
    """Converts a batch of items on a thread-pool thread."""

    def __init__(self, items: List[ConversionItem], options: ConverterOptions):
        super().__init__()
        self.items = items
        self.options = options
        self.signals = WorkerSignals()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @Slot()
    def run(self) -> None:
        # Building MarkItDown can be slow (model load) -- do it off the UI thread.
        md = build_markitdown(self.options)
        total = len(self.items)
        for index, item in enumerate(self.items):
            if self._cancelled:
                break
            convert_item(md, item, self.options)
            self.signals.item_done.emit(index, item)
            self.signals.progress.emit(index + 1, total)
        self.signals.finished.emit()
