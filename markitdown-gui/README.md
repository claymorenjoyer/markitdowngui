# MarkItDown GUI

A cross-platform desktop front-end for [MarkItDown](https://github.com/microsoft/markitdown).
Convert PDF, Office documents, images, audio, HTML, URLs and more to Markdown — with
drag-and-drop, batch conversion, a live preview, and one-click saving.

Built with [PySide6](https://doc.qt.io/qtforpython/) (Qt), so it runs on macOS, Windows, and Linux.

## Download

Pre-built apps for each platform are attached to the
[Releases](../../releases) page:

| Platform | File |
| --- | --- |
| macOS (Apple Silicon) | `MarkItDownGUI-macos-arm64.zip` (unzip → `MarkItDownGUI.app`) |
| Windows | `MarkItDownGUI-windows.zip` (unzip → `MarkItDownGUI.exe`) |
| Linux | `MarkItDownGUI-linux.zip` (unzip → run `MarkItDownGUI`) |

### Opening unsigned builds

These builds are **not code-signed** (that requires paid Apple/Microsoft developer
accounts), so the OS may warn you the first time:

- **macOS:** right-click `MarkItDownGUI.app` → **Open** → **Open**. Only needed once.
- **Windows:** on the SmartScreen prompt click **More info** → **Run anyway**.

## Features

- Add files, paste a URL, or drag-and-drop files onto the window
- Batch conversion with per-item status and a progress bar
- **Markdown Source** and rendered **Preview** tabs
- Save current as `.md`, save all to a folder, or copy to clipboard
- Options (with hover help): enable 3rd-party plugins, keep data URIs

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

## Build a standalone executable

```bash
cd markitdown-gui
./build.sh          # output in dist/
```

`build.sh` uses `build.spec`, which bundles the data files MarkItDown needs
(magika models, PDF CMaps, Office templates, etc.). PyInstaller cannot
cross-compile — run it on each target OS, or use the GitHub Actions workflow
at `.github/workflows/build-gui.yml`, which builds all three platforms and
attaches them to a Release when you push a `gui-v*` tag.
