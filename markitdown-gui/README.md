# MarkItDown GUI

**A cross-platform desktop application that brings [MarkItDown](https://github.com/microsoft/markitdown) to everyone — no command line required.**

Convert PDFs, Word documents, Excel sheets, PowerPoint decks, HTML pages, images (via OCR), audio files (via transcription), and more into clean, structured Markdown. Built for researchers, content teams, technical writers, and anyone preparing documents for LLMs and AI workflows.

---

## Why a GUI for MarkItDown?

[MarkItDown](https://github.com/microsoft/markitdown) is an excellent Python library, but using it demands comfort with terminals, Python environments, and scripting. That limits who can benefit from it.

**This project bridges that gap.** It wraps MarkItDown in a native desktop interface that lets you:

- **Drag and drop** files instead of typing paths
- **Batch-convert** dozens of documents in one click
- **Preview** the Markdown output instantly — rendered side-by-side with the raw source
- **Save** individual results or export an entire batch to a folder
- **Copy** converted Markdown straight to the clipboard for pasting into ChatGPT, Claude, or your notes

It's built for the workflows real people have: migrating documentation, preparing training data for LLMs, archiving web content, or extracting text from mixed-format document collections.

| Without GUI | With MarkItDown GUI |
|---|---|
| Write Python scripts per batch | Click "Add Files" or drag-and-drop |
| Manually handle errors in code | See per-file status inline (Done / Error) |
| No live preview | Side-by-side Markdown source + rendered preview |
| CLI-only, context-switch to view output | Everything in one window |

---

## Download

Pre-built apps for each platform are attached to the [Releases](../../releases) page:

| Platform | File |
| --- | --- |
| macOS (Apple Silicon) | `MarkItDownGUI-macos-arm64.zip` (unzip → `MarkItDownGUI.app`) |
| Windows | `MarkItDownGUI-windows.zip` (unzip → `MarkItDownGUI.exe`) |
| Linux | `MarkItDownGUI-linux.zip` (unzip → run `MarkItDownGUI`) |

### Opening unsigned builds

These builds are **not code-signed** (that requires paid Apple/Microsoft developer accounts), so the OS may warn you the first time:

- **macOS:** right-click `MarkItDownGUI.app` → **Open** → **Open**. Only needed once.
- **Windows:** on the SmartScreen prompt click **More info** → **Run anyway**.

---

## Features

- **Broad format support** — PDF, DOCX, PPTX, XLSX, HTML, images (OCR), audio (speech-to-text), CSV, JSON, XML, ZIP, and more (inherits all MarkItDown converters)
- **Batch conversion** — queue many files and URLs, convert them all in one go
- **Non-blocking UI** — conversion runs on a background thread; the interface stays responsive and shows live progress
- **Drag-and-drop** — drop files directly onto the file list
- **URL support** — paste any HTTP/HTTPS URL to convert web content to Markdown
- **Markdown preview** — toggle between raw Markdown source and rendered HTML preview
- **Export options** — save individual `.md` files or export all successful conversions to a folder at once
- **Configurable options** — toggle third-party MarkItDown plugins and control whether inline base64 data URIs are kept
- **Copy to clipboard** — one-click copy for pasting directly into an LLM or notes
- **Cross-platform** — runs on macOS, Windows, and Linux (PySide6 / Qt 6)
- **Standalone builds** — pre-built app bundles for all three platforms via GitHub Actions (no Python install needed)

---

## Run from source

Requires Python 3.10+.

```bash
cd markitdown-gui
./run.sh            # macOS / Linux: creates .venv and launches
```

On Windows:

```bat
cd markitdown-gui
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app\main.py
```

To validate that the build works end-to-end:

```bash
python app/main.py --selftest
# prints "SELFTEST OK" on success
```

---

## Usage

1. **Add files** — Click *Add Files...* or drag-and-drop documents onto the left panel. You can also use *Add URL...* to convert a web page.
2. **Configure options** (optional) — Enable third-party plugins or choose to keep inline base64 data URIs.
3. **Convert** — Click *Convert All*. Progress is shown in the status bar. Each item shows `[Done]` or `[Error]` when finished.
4. **Review** — Click an item in the list to see its Markdown source and rendered preview in the right-hand tabs.
5. **Export** — Use *Save Current as .md...*, *Save All to Folder...*, or *Copy to Clipboard*.

---

## Build a standalone executable

```bash
cd markitdown-gui
./build.sh          # output in dist/
```

`build.sh` uses `build.spec`, which bundles the data files MarkItDown needs (magika models, PDF CMaps, Office templates, etc.). PyInstaller cannot cross-compile — run it on each target OS, or use the GitHub Actions workflow at `.github/workflows/build-gui.yml`, which builds all three platforms and attaches them to a Release when you push a `gui-v*` tag.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **UI Framework** | [PySide6](https://pypi.org/project/PySide6/) (Qt 6 for Python) |
| **Conversion Engine** | [MarkItDown](https://github.com/microsoft/markitdown) |
| **Concurrency** | Qt `QThreadPool` + `QRunnable` — background conversion keeps the UI responsive |
| **Packaging** | [PyInstaller](https://pyinstaller.org/) — produces standalone app bundles for each platform |
| **CI / CD** | GitHub Actions — multi-platform builds on `gui-v*` tags |
| **Language** | Python 3.10+ |

---

## Project Architecture

```
markitdown-gui/
├── app/
│   ├── main.py         # Application entry point, MainWindow, file-list UI, menus, self-test
│   ├── converter.py    # Thin wrapper around MarkItDown: ConversionItem, ConverterOptions, convert_item()
│   └── worker.py       # Background QRunnable worker — runs conversion off the UI thread, emits signals
├── build.spec          # PyInstaller spec for bundling into standalone executables
├── build.sh            # One-command build script (macOS / Linux)
├── run.sh              # One-command launch script
├── requirements.txt    # Python dependencies
└── README.md
```

### Design decisions

- **Separation of concerns** — `converter.py` knows nothing about Qt; it's plain Python. `worker.py` bridges the converter into the Qt threading model via signals. `main.py` owns all UI state and wiring.
- **Background threading** — building a `MarkItDown` instance and running conversions can be slow (model loading, network calls for URLs). Everything runs on a `QThreadPool` thread so the UI never freezes.
- **Mutable items with signals** — each `ConversionItem` is mutated in-place by the worker; `item_done` signals carry the index so the UI refreshes just that row. No global state manager needed.
- **Packaging** — the PyInstaller spec (`build.spec`) carefully collects hidden imports and data files from markitdown, magika (ML models), onnxruntime, pdfminer, and other dependencies that static analysis would miss.

---

## Contributing

This is a personal project built for learning and practical use. Feedback and contributions are welcome — feel free to open an issue or pull request.

Areas I'd like to explore next:
- Dark / light theme toggle
- Per-format conversion options (e.g., OCR language selection)
- Drag-and-drop reordering of the conversion queue
- Image / screenshot in the readme

---

*Built with PySide6 + MarkItDown | July 2025*
