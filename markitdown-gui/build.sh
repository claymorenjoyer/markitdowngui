#!/usr/bin/env bash
# Build a standalone, distributable MarkItDown GUI using PyInstaller.
#
#   macOS   -> dist/MarkItDownGUI.app  (double-clickable bundle)
#   all OS  -> dist/MarkItDownGUI/      (folder with the native executable)
#
# PyInstaller cannot cross-compile: run this on each OS you want a build for,
# or let the GitHub Actions workflow (.github/workflows/build-gui.yml) do all three.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  ./.venv/bin/python -m pip install --upgrade pip
fi
./.venv/bin/python -m pip install -r requirements.txt pyinstaller

./.venv/bin/pyinstaller build.spec --noconfirm --clean

echo
echo "Build complete. Output in: $DIR/dist"
if [ -d "$DIR/dist/MarkItDownGUI.app" ]; then
  echo "macOS app bundle: dist/MarkItDownGUI.app"
  echo "Zip for distribution:  ditto -c -k --keepParent dist/MarkItDownGUI.app dist/MarkItDownGUI-macos.zip"
fi
