"""MarkItDown GUI - a cross-platform desktop front-end for the markitdown library."""

from __future__ import annotations

import sys
from typing import List, Optional

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from converter import ConversionItem, ConverterOptions
from worker import ConversionWorker


STATUS_PENDING = "Pending"
STATUS_RUNNING = "Converting..."
STATUS_DONE = "Done"
STATUS_ERROR = "Error"


class FileListWidget(QListWidget):
    """A list that also accepts dropped files."""

    def __init__(self, on_paths_dropped):
        super().__init__()
        self._on_paths_dropped = on_paths_dropped
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            super().dropEvent(event)
            return
        paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
        paths = [p for p in paths if p]
        if paths:
            self._on_paths_dropped(paths)
            event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MarkItDown GUI")
        self.resize(1000, 680)

        self.items: List[ConversionItem] = []
        self.pool = QThreadPool.globalInstance()
        self._worker: Optional[ConversionWorker] = None

        self._build_ui()
        self._build_menu()

    # ---------- UI construction ----------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # Left panel: inputs + queue.
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("Files / URLs to convert"))

        self.list_widget = FileListWidget(self.add_paths)
        self.list_widget.currentRowChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.list_widget, 1)

        btn_row = QHBoxLayout()
        self.add_files_btn = QPushButton("Add Files...")
        self.add_files_btn.clicked.connect(self.choose_files)
        self.add_url_btn = QPushButton("Add URL...")
        self.add_url_btn.clicked.connect(self.choose_url)
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_all)
        for b in (self.add_files_btn, self.add_url_btn, self.remove_btn, self.clear_btn):
            btn_row.addWidget(b)
        left_layout.addLayout(btn_row)

        # Options.
        self.plugins_cb = QCheckBox("Enable 3rd-party plugins")
        plugins_tip = (
            "Load 3rd-party MarkItDown plugins installed in your Python "
            "environment.\n\n"
            "Plugins can add support for extra file formats or custom "
            "conversion behavior. Disabled by default — only enable this "
            "if you have installed plugins that you trust."
        )
        left_layout.addLayout(self._option_row(self.plugins_cb, plugins_tip))

        self.data_uris_cb = QCheckBox("Keep data URIs (base64 images)")
        data_uris_tip = (
            "Keep embedded data URIs (such as base64-encoded inline images) "
            "in the Markdown output.\n\n"
            "When disabled, these are truncated so the output stays small and "
            "readable. Enable this if you need the full embedded image data "
            "preserved in the result."
        )
        left_layout.addLayout(self._option_row(self.data_uris_cb, data_uris_tip))

        self.convert_btn = QPushButton("Convert All")
        self.convert_btn.clicked.connect(self.start_conversion)
        left_layout.addWidget(self.convert_btn)

        splitter.addWidget(left)

        # Right panel: output tabs.
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        mono = QFont("Menlo")
        mono.setStyleHint(QFont.Monospace)

        self.source_view = QPlainTextEdit()
        self.source_view.setReadOnly(True)
        self.source_view.setFont(mono)
        self.source_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.tabs.addTab(self.source_view, "Markdown Source")

        self.preview_view = QTextBrowser()
        self.preview_view.setOpenExternalLinks(True)
        self.tabs.addTab(self.preview_view, "Preview")

        right_layout.addWidget(self.tabs, 1)

        save_row = QHBoxLayout()
        self.save_btn = QPushButton("Save Current as .md...")
        self.save_btn.clicked.connect(self.save_current)
        self.save_all_btn = QPushButton("Save All to Folder...")
        self.save_all_btn.clicked.connect(self.save_all)
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_current)
        for b in (self.save_btn, self.save_all_btn, self.copy_btn):
            save_row.addWidget(b)
        right_layout.addLayout(save_row)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 680])

        # Status bar with progress.
        status = QStatusBar()
        self.setStatusBar(status)
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(220)
        self.progress.setVisible(False)
        status.addPermanentWidget(self.progress)
        self.status_label = QLabel("Add files or a URL to begin.")
        status.addWidget(self.status_label)

        self._update_buttons()

    def _option_row(self, checkbox: QCheckBox, tooltip: str) -> QHBoxLayout:
        """A checkbox followed by a hoverable '?' help icon, both sharing a tooltip."""
        checkbox.setToolTip(tooltip)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(checkbox)
        row.addWidget(self._make_help_icon(tooltip))
        row.addStretch(1)
        return row

    @staticmethod
    def _make_help_icon(tooltip: str) -> QLabel:
        icon = QLabel("?")
        icon.setToolTip(tooltip)
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(16, 16)
        icon.setCursor(Qt.WhatsThisCursor)
        icon.setStyleSheet(
            "QLabel {"
            " border: 1px solid palette(mid);"
            " border-radius: 8px;"
            " color: palette(text);"
            " font-weight: bold;"
            " font-size: 11px;"
            "}"
        )
        return icon

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        open_action = QAction("Add Files...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.choose_files)
        file_menu.addAction(open_action)

        url_action = QAction("Add URL...", self)
        url_action.triggered.connect(self.choose_url)
        file_menu.addAction(url_action)

        file_menu.addSeparator()

        save_action = QAction("Save Current as .md...", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_current)
        file_menu.addAction(save_action)

        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

    # ---------- input management ----------

    def choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Select files to convert")
        if paths:
            self.add_paths(paths)

    def choose_url(self) -> None:
        url, ok = QInputDialog.getText(self, "Add URL", "Enter a URL (http/https):")
        if ok and url.strip():
            self.add_url(url.strip())

    def add_paths(self, paths: List[str]) -> None:
        for path in paths:
            self.items.append(ConversionItem(source=path, is_url=False))
        self._refresh_list()
        self.status_label.setText(f"{len(self.items)} item(s) queued.")

    def add_url(self, url: str) -> None:
        self.items.append(ConversionItem(source=url, is_url=True))
        self._refresh_list()
        self.status_label.setText(f"{len(self.items)} item(s) queued.")

    def remove_selected(self) -> None:
        rows = sorted((i.row() for i in self.list_widget.selectedIndexes()), reverse=True)
        for row in rows:
            if 0 <= row < len(self.items):
                del self.items[row]
        self._refresh_list()

    def clear_all(self) -> None:
        self.items.clear()
        self._refresh_list()
        self.source_view.clear()
        self.preview_view.clear()

    def _refresh_list(self) -> None:
        current = self.list_widget.currentRow()
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for item in self.items:
            status = self._status_for(item)
            lw = QListWidgetItem(f"{item.display_name}    [{status}]")
            self.list_widget.addItem(lw)
        self.list_widget.blockSignals(False)
        if 0 <= current < len(self.items):
            self.list_widget.setCurrentRow(current)
        self._update_buttons()

    @staticmethod
    def _status_for(item: ConversionItem) -> str:
        if item.error:
            return STATUS_ERROR
        if item.markdown is not None:
            return STATUS_DONE
        return STATUS_PENDING

    # ---------- conversion ----------

    def start_conversion(self) -> None:
        if not self.items:
            return
        options = ConverterOptions(
            enable_plugins=self.plugins_cb.isChecked(),
            keep_data_uris=self.data_uris_cb.isChecked(),
        )
        # Reset prior results.
        for item in self.items:
            item.markdown = None
            item.title = None
            item.error = None
        self._refresh_list()

        self._set_running(True)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(self.items))
        self.progress.setValue(0)

        worker = ConversionWorker(self.items, options)
        worker.signals.item_done.connect(self._on_item_done)
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self._on_finished)
        self._worker = worker
        self.pool.start(worker)

    def _on_item_done(self, index: int, item: ConversionItem) -> None:
        # item is the same object already in self.items; just refresh its row.
        self._refresh_list()
        if index == self.list_widget.currentRow():
            self._show_item(item)

    def _on_progress(self, done: int, total: int) -> None:
        self.progress.setValue(done)
        self.status_label.setText(f"Converting {done}/{total}...")

    def _on_finished(self) -> None:
        self._set_running(False)
        self.progress.setVisible(False)
        ok = sum(1 for i in self.items if i.succeeded)
        failed = sum(1 for i in self.items if i.error)
        self.status_label.setText(f"Finished: {ok} succeeded, {failed} failed.")
        # Show first result if nothing selected.
        if self.list_widget.currentRow() < 0 and self.items:
            self.list_widget.setCurrentRow(0)

    def _set_running(self, running: bool) -> None:
        self.convert_btn.setEnabled(not running)
        self.add_files_btn.setEnabled(not running)
        self.add_url_btn.setEnabled(not running)
        self.remove_btn.setEnabled(not running)
        self.clear_btn.setEnabled(not running)

    # ---------- output display ----------

    def _on_selection_changed(self, row: int) -> None:
        if 0 <= row < len(self.items):
            self._show_item(self.items[row])
        else:
            self.source_view.clear()
            self.preview_view.clear()

    def _show_item(self, item: ConversionItem) -> None:
        if item.error:
            self.source_view.setPlainText(f"Conversion failed:\n\n{item.error}")
            self.preview_view.setPlainText(f"Conversion failed:\n\n{item.error}")
        elif item.markdown is not None:
            self.source_view.setPlainText(item.markdown)
            self.preview_view.setMarkdown(item.markdown)
        else:
            self.source_view.setPlainText("(not converted yet)")
            self.preview_view.clear()

    # ---------- saving ----------

    def _current_item(self) -> Optional[ConversionItem]:
        row = self.list_widget.currentRow()
        if 0 <= row < len(self.items):
            return self.items[row]
        return None

    def save_current(self) -> None:
        item = self._current_item()
        if item is None or not item.succeeded:
            QMessageBox.information(self, "Nothing to save", "Select a converted item first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Markdown", item.suggested_filename(), "Markdown (*.md)"
        )
        if path:
            self._write_file(path, item.markdown)
            self.status_label.setText(f"Saved {path}")

    def save_all(self) -> None:
        done = [i for i in self.items if i.succeeded]
        if not done:
            QMessageBox.information(self, "Nothing to save", "No successful conversions yet.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Choose output folder")
        if not folder:
            return
        import os

        saved = 0
        for item in done:
            target = os.path.join(folder, item.suggested_filename())
            # Avoid clobbering duplicates.
            base, ext = os.path.splitext(target)
            n = 1
            while os.path.exists(target):
                target = f"{base}_{n}{ext}"
                n += 1
            self._write_file(target, item.markdown)
            saved += 1
        self.status_label.setText(f"Saved {saved} file(s) to {folder}")

    def copy_current(self) -> None:
        item = self._current_item()
        if item is None or not item.succeeded:
            return
        QApplication.clipboard().setText(item.markdown)
        self.status_label.setText("Copied markdown to clipboard.")

    def _write_file(self, path: str, text: str) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))

    def _update_buttons(self) -> None:
        has_items = bool(self.items)
        self.convert_btn.setEnabled(has_items)
        self.clear_btn.setEnabled(has_items)


def _run_selftest() -> int:
    """Convert a built-in sample and report success. Used to validate packaged builds."""
    import os
    import tempfile
    from converter import ConversionItem, ConverterOptions, build_markitdown, convert_item

    sample = os.path.join(tempfile.gettempdir(), "_markitdown_selftest.csv")
    with open(sample, "w", encoding="utf-8") as f:
        f.write("name,age\nAlice,30\nBob,25\n")
    options = ConverterOptions()
    md = build_markitdown(options)
    item = ConversionItem(source=sample)
    convert_item(md, item, options)
    if item.succeeded and "Alice" in (item.markdown or ""):
        sys.stderr.write("SELFTEST OK\n")
        return 0
    sys.stderr.write(f"SELFTEST FAILED: {item.error or 'no markdown'}\n")
    return 1


def main() -> int:
    if "--selftest" in sys.argv:
        return _run_selftest()
    app = QApplication(sys.argv)
    app.setApplicationName("MarkItDown GUI")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
