"""Colored, human readable logs for the node and the web gateway.

Each record may carry a ``tone`` (``ok``, ``bad``, ``warn`` or ``info``) that
selects the color of its label. Colors are enabled when the stream is a
terminal or when ``ECOORIGEM_LOG_COLOR`` is set, and disabled by ``NO_COLOR``.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import IO

RESET = "\033[0m"
DIM = "\033[2m"
TONES = {
    "ok": "\033[1;32m",
    "bad": "\033[1;31m",
    "warn": "\033[1;33m",
    "info": "\033[1;36m",
}
LOGGER_NAME = "ecoorigem"


def color_enabled(stream: IO[str]) -> bool:
    """Decide whether ANSI colors should be written to ``stream``."""
    if os.environ.get("NO_COLOR"):
        return False
    forced = os.environ.get("ECOORIGEM_LOG_COLOR", "").strip().lower()
    if forced in {"1", "true", "yes", "on", "sim"}:
        return True
    if forced in {"0", "false", "no", "off", "nao", "não"}:
        return False
    return bool(getattr(stream, "isatty", lambda: False)())


class ToneFormatter(logging.Formatter):
    """Format records as ``HH:MM:SS LABEL message`` with an optional color."""

    def __init__(self, color: bool) -> None:
        super().__init__(datefmt="%H:%M:%S")
        self.color = color

    def format(self, record: logging.LogRecord) -> str:
        tone = getattr(record, "tone", "info")
        label = getattr(record, "label", record.levelname)
        stamp = self.formatTime(record, self.datefmt)
        text = record.getMessage()
        if not self.color:
            return f"{stamp} {label:<10} {text}"
        return (
            f"{DIM}{stamp}{RESET} {TONES.get(tone, TONES['info'])}{label:<10}{RESET} "
            f"{text}"
        )


def get_logger(component: str) -> logging.Logger:
    """Return the logger of one component (``node`` or ``web``)."""
    return logging.getLogger(f"{LOGGER_NAME}.{component}")


def configure_logging(stream: IO[str] | None = None) -> logging.Handler:
    """Send the project logs to ``stream`` and quiet the HTTP access log.

    The access log of every request is noisy because the interface polls the
    node. Set ``ECOORIGEM_ACCESS_LOG=1`` to keep it.
    """
    stream = stream or sys.stdout
    handler = logging.StreamHandler(stream)
    handler.setFormatter(ToneFormatter(color_enabled(stream)))
    root = logging.getLogger(LOGGER_NAME)
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    root.propagate = False
    access = os.environ.get("ECOORIGEM_ACCESS_LOG", "").strip().lower()
    if access not in {"1", "true", "yes", "on", "sim"}:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
    return handler
