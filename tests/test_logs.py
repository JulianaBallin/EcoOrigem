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
from ecoorigem.node import LedgerNode, LedgerStore, narration
from tests.conftest import TEST_DIFFICULTY, VALID_LOT, Client

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


def _events(caplog) -> dict[str, dict[str, str]]:
    """Map each node log title to its details."""
    return {
        r.label: dict(r.details)
        for r in caplog.records
        if r.name == f"{LOGGER_NAME}.node"
    }


def test_node_logs_confirmed_blocks_in_plain_language(deployed, wallets, caplog):
    client = deployed()
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    client.call(wallets["produtor"], "register_lot", VALID_LOT)
    client.call(
        wallets["beneficiador"],
        "record_processing",
        {"lot_id": "LOT-0001", "description": "Despolpamento."},
    )
    events = _events(caplog)
    registered = events["BLOCO #6 CONFIRMADO"]
    assert registered["Quem"].startswith("Produtor (0x")
    assert registered["Ação"] == "registrou o lote LOT-0001 (Açaí, 250,5 kg)"
    assert registered["Status"] == "novo para CADASTRADO"
    processed = events["BLOCO #7 CONFIRMADO"]
    assert processed["Ação"] == "registrou o beneficiamento do lote LOT-0001"
    assert processed["Status"] == "CADASTRADO para BENEFICIADO"
    assert "tentativas em" in processed["Prova de trabalho"]
    assert processed["Índice"] == "7"
    assert processed["Hash"].startswith("0" * TEST_DIFFICULTY)
    assert len(processed["Hash anterior"]) == 64
    assert processed["Nonce"].isdigit()
    assert processed["Dados"].startswith("record_processing (transação ")
    assert "  lot_id: LOT-0001" in processed["Dados"]
    assert processed["Encadeamento"] == ("hash anterior confere com o hash do bloco #6")


def test_node_logs_rejections_in_plain_language(deployed, wallets, caplog):
    client = deployed()
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    with pytest.raises(AccessDeniedError):
        client.call(wallets["intruso"], "register_lot", VALID_LOT)
    record = next(r for r in caplog.records if r.label == "OPERAÇÃO REJEITADA")
    details = dict(record.details)
    assert record.tone == "bad" and record.levelno == logging.WARNING
    assert details["Quem"].startswith("Carteira sem perfil (0x")
    assert details["Tentou"] == "registrar um lote"
    assert details["Código"] == "ACCESS_DENIED"
    assert details["Resultado"] == "nenhum bloco criado, contrato inalterado"


def test_node_names_the_administrator_and_role_grants(client, wallets, caplog):
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    client.deploy(wallets["administrador"])
    client.call(
        wallets["administrador"],
        "grant_role",
        {"account": wallets["produtor"].address, "role": "PRODUCER"},
    )
    events = _events(caplog)
    assert events["BLOCO #1 CONFIRMADO"]["Ação"] == "implantou o contrato EcoOrigem"
    grant = events["BLOCO #2 CONFIRMADO"]
    assert grant["Quem"].startswith("Administrador (0x")
    assert grant["Ação"].startswith("concedeu o perfil Produtor para 0x")


def test_node_logs_manual_mining(tmp_path, clock, wallets, caplog):
    node = LedgerNode(
        LedgerStore(tmp_path / "manual"), TEST_DIFFICULTY, auto_mine=False, clock=clock
    )
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    Client(node, clock).deploy(wallets["administrador"])
    node.mine_pending()
    events = _events(caplog)
    assert events["TRANSAÇÃO PENDENTE"]["Resultado"] == "aguardando a mineração manual"
    mined = events["BLOCO #1 MINERADO"]
    assert mined["Transações"] == "1"
    assert mined["Hash anterior"] == node.chain.blocks[0].hash


def test_node_logs_tampering_and_restore(deployed, node, caplog):
    deployed()
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    node.lab_tamper(1, {"note": "alterado"})
    node.lab_restore()
    events = _events(caplog)
    assert events["ADULTERAÇÃO DETECTADA"]["Primeiro inválido"] == "#1"
    assert events["CADEIA RESTAURADA"]["Integridade"] == "válida"


def test_formatter_prints_indented_blocks():
    record = _record("ok", "BLOCO #2 CONFIRMADO")
    record.msg = ""
    record.details = [("Quem", "Produtor"), ("Status", "novo para CADASTRADO")]
    lines = ToneFormatter(color=False).format(record).split("\n")
    assert lines[0] == "" and lines[1].endswith("  BLOCO #2 CONFIRMADO")
    assert lines[2] == " " * 10 + "Quem    Produtor"
    assert lines[3] == " " * 10 + "Status  novo para CADASTRADO"


def test_numbers_use_brazilian_format():
    assert narration.number(36291) == "36.291"
    assert narration.number(0.19, 2) == "0,19"
    assert narration.short(None) == "desconhecido"


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


def test_formatter_aligns_multi_line_values():
    record = _record("ok", "BLOCO #3")
    record.msg = ""
    record.details = [("Dados", "register_lot\n  product: Açaí"), ("Nonce", "7")]
    lines = ToneFormatter(color=False).format(record).split("\n")
    assert lines[2] == " " * 10 + "Dados  register_lot"
    assert lines[3] == " " * 10 + " " * 7 + "  product: Açaí"


def test_link_reports_genesis_and_broken_chain(deployed, node):
    deployed()
    genesis, first = node.chain.blocks[0], node.chain.blocks[1]
    assert narration.link(genesis, None) == "bloco gênesis, sem bloco anterior"
    assert narration.link(first, genesis).startswith("hash anterior confere")
    assert narration.link(genesis, first).startswith("QUEBRADO")
    assert narration.block_data(genesis) == (genesis.note or "sem transações")
