#!/usr/bin/env bash
# Launch the MarkItDown GUI. Creates a local virtual environment on first run.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment (.venv) and installing dependencies..."
  python3 -m venv .venv
  ./.venv/bin/python -m pip install --upgrade pip
  ./.venv/bin/python -m pip install -r requirements.txt
fi

exec ./.venv/bin/python app/main.py
