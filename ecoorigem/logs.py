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
    """Format records as a colored title followed by indented details.

    A record with ``details`` (a list of ``(field, value)`` pairs) becomes a
    block separated from the previous one by a blank line::

        15:25:40  BLOCO #22 CONFIRMADO
                  Quem       Beneficiador (0x1665...3d3d)
                  Status     CADASTRADO para BENEFICIADO

    Records without details stay on a single line.
    """

    indent = " " * 10

    def __init__(self, color: bool) -> None:
        super().__init__(datefmt="%H:%M:%S")
        self.color = color

    def _paint(self, code: str, text: str) -> str:
        return f"{code}{text}{RESET}" if self.color else text

    def format(self, record: logging.LogRecord) -> str:
        tone = getattr(record, "tone", "info")
        label = getattr(record, "label", record.levelname)
        details = getattr(record, "details", None)
        stamp = self.formatTime(record, self.datefmt)
        text = record.getMessage()
        if not details:
            color = TONES.get(tone, TONES["info"])
            head = f"{self._paint(DIM, stamp)}  {self._paint(color, f'{label:<10}')}"
            return f"{head} {text}".rstrip()
        return "\n" + self.render(stamp, tone, label, details, text)

    def render(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        stamp: str,
        tone: str,
        title: str,
        details: list[tuple[str, str]],
        text: str = "",
    ) -> str:
        """Render a titled block. Multi-line values stay aligned in their column."""
        color = TONES.get(tone, TONES["info"])
        width = max(len(field) for field, _ in details) + 2
        lines = [f"{self._paint(DIM, stamp)}  {self._paint(color, title)}"]
        if text:
            lines.append(f"{self.indent}{text}")
        for field, value in details:
            first, *rest = str(value).split("\n") or [""]
            lines.append(f"{self.indent}{self._paint(DIM, f'{field:<{width}}')}{first}")
            lines.extend(f"{self.indent}{' ' * width}{line}" for line in rest)
        return "\n".join(lines)


def log_event(  # pylint: disable=too-many-arguments
    logger: logging.Logger,
    tone: str,
    event: tuple[str, list[tuple[str, str]]],
    *,
    level: int = logging.INFO,
) -> None:
    """Log a titled block of details, as built by :mod:`ecoorigem.node.narration`."""
    title, details = event
    logger.log(level, "", extra={"tone": tone, "label": title, "details": details})


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
