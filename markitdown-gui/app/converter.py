"""Thin wrapper around the MarkItDown library."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from markitdown import (
    MarkItDown,
    StreamInfo,
    MarkItDownException,
)


@dataclass
class ConversionItem:
    """A single input to convert: either a local file path or a URL."""

    source: str
    is_url: bool = False

    # Filled in after conversion.
    markdown: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None

    @property
    def display_name(self) -> str:
        if self.is_url:
            return self.source
        return os.path.basename(self.source) or self.source

    @property
    def succeeded(self) -> bool:
        return self.markdown is not None and self.error is None

    def suggested_filename(self) -> str:
        if self.is_url:
            base = "".join(c if c.isalnum() else "_" for c in self.display_name)
            base = base.strip("_")[:60] or "output"
        else:
            base = os.path.splitext(os.path.basename(self.source))[0] or "output"
        return base + ".md"


@dataclass
class ConverterOptions:
    enable_plugins: bool = False
    keep_data_uris: bool = False


def build_markitdown(options: ConverterOptions) -> MarkItDown:
    """Construct a MarkItDown instance for the given options."""
    return MarkItDown(enable_plugins=options.enable_plugins)


def convert_item(
    md: MarkItDown, item: ConversionItem, options: ConverterOptions
) -> ConversionItem:
    """Convert a single item in place, capturing markdown or an error string."""
    try:
        result = md.convert(item.source, keep_data_uris=options.keep_data_uris)
        item.markdown = result.markdown
        item.title = result.title
        item.error = None
    except MarkItDownException as exc:
        item.markdown = None
        item.error = _format_exception(exc)
    except FileNotFoundError:
        item.markdown = None
        item.error = "File not found."
    except Exception as exc:  # noqa: BLE001 - surface anything to the UI
        item.markdown = None
        item.error = f"{type(exc).__name__}: {exc}"
    return item


def _format_exception(exc: Exception) -> str:
    msg = str(exc).strip()
    if not msg:
        return type(exc).__name__
    # Keep it to the first few lines so the UI stays readable.
    lines = [ln for ln in msg.splitlines() if ln.strip()]
    return "\n".join(lines[:6])
