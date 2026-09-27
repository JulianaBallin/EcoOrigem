"""Tests for the colored logs of the node and the web gateway."""

from __future__ import annotations

import io
import logging

import pytest

from ecoorigem.errors import AccessDeniedError
from ecoorigem.logs import (
    LOGGER_NAME,
    TONES,
    ToneFormatter,
    color_enabled,
    configure_logging,
)
from tests.conftest import VALID_LOT

# The web fixtures are reused by name, so pylint sees them as unused.
# pylint: disable-next=unused-import
from tests.test_web import LOT, ready_fixture, stack_fixture


class _Tty(io.StringIO):
    def isatty(self) -> bool:
        return True


def _record(tone: str = "ok", label: str = "BLOCO") -> logging.LogRecord:
    record = logging.LogRecord("ecoorigem.node", logging.INFO, "", 0, "msg", (), None)
    record.tone = tone
    record.label = label
    return record


@pytest.fixture(name="restore_loggers")
def restore_loggers_fixture():
    """Undo the global logging changes made by ``configure_logging``."""
    project = logging.getLogger(LOGGER_NAME)
    werkzeug = logging.getLogger("werkzeug")
    saved = (project.handlers[:], project.level, project.propagate, werkzeug.level)
    yield
    project.handlers, project.level, project.propagate = saved[0], saved[1], saved[2]
    werkzeug.setLevel(saved[3])


@pytest.mark.parametrize(
    ("env", "tty", "expected"),
    [
        ({}, True, True),
        ({}, False, False),
        ({"ECOORIGEM_LOG_COLOR": "1"}, False, True),
        ({"ECOORIGEM_LOG_COLOR": "0"}, True, False),
        ({"ECOORIGEM_LOG_COLOR": "1", "NO_COLOR": "1"}, True, False),
    ],
)
def test_color_is_decided_by_terminal_and_environment(monkeypatch, env, tty, expected):
    for name in ("ECOORIGEM_LOG_COLOR", "NO_COLOR"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    stream = _Tty() if tty else io.StringIO()
    assert color_enabled(stream) is expected


def test_formatter_colors_the_label_by_tone():
    colored = ToneFormatter(color=True).format(_record("bad", "REJEITADA"))
    assert TONES["bad"] in colored and "REJEITADA" in colored and "msg" in colored
    plain = ToneFormatter(color=False).format(_record())
    assert "\033[" not in plain and "BLOCO" in plain


@pytest.mark.usefixtures("restore_loggers")
def test_configure_logging_writes_colored_lines(monkeypatch):
    monkeypatch.setenv("ECOORIGEM_LOG_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("ECOORIGEM_ACCESS_LOG", raising=False)
    stream = io.StringIO()
    configure_logging(stream)
    logging.getLogger(f"{LOGGER_NAME}.node").info(
        "Bloco #1", extra={"tone": "ok", "label": "BLOCO"}
    )
    assert TONES["ok"] in stream.getvalue() and "Bloco #1" in stream.getvalue()
    assert logging.getLogger("werkzeug").level == logging.WARNING


def test_node_logs_mined_blocks_and_rejections(deployed, wallets, caplog):
    client = deployed()
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    client.call(wallets["produtor"], "register_lot", VALID_LOT)
    with pytest.raises(AccessDeniedError):
        client.call(wallets["intruso"], "register_lot", VALID_LOT)
    tones = {(r.label, r.tone) for r in caplog.records}
    assert ("BLOCO", "ok") in tones and ("REJEITADA", "bad") in tones
    text = caplog.text
    assert "register_lot" in text and "ACCESS_DENIED" in text


def test_node_logs_tampering_and_restore(deployed, node, caplog):
    deployed()
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    node.lab_tamper(1, {"note": "alterado"})
    node.lab_restore()
    labels = [(r.label, r.tone) for r in caplog.records]
    assert ("INTEGRIDADE", "warn") in labels and ("INTEGRIDADE", "ok") in labels


def test_web_logs_sends_confirmations_and_rejections(ready, caplog):
    _, _, web = ready
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    web.post(
        "/api/send", json={"wallet": "produtor", "method": "register_lot", "args": LOT}
    )
    web.post(
        "/api/send", json={"wallet": "intruso", "method": "register_lot", "args": LOT}
    )
    labels = [r.label for r in caplog.records if r.name == f"{LOGGER_NAME}.web"]
    assert labels == ["ENVIO", "CONFIRMADA", "ENVIO", "REJEITADA"]
