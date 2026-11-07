"""Integration tests: command line and HTTP client against a live node."""

from __future__ import annotations

import threading

import pytest
from werkzeug.serving import make_server

from ecoorigem.__main__ import build_parser, main
from ecoorigem.bootstrap import build_node, build_web
from ecoorigem.client import (
    NodeClient,
    NodeUnavailableError,
    RemoteRejectionError,
    http_transport,
)
from ecoorigem.config import Settings
from ecoorigem.errors import ContractNotDeployedError
from ecoorigem.keystore import Keystore


@pytest.fixture(name="live")
def live_fixture(tmp_path, monkeypatch):
    """A real node listening on an ephemeral port, configured through env vars."""
    monkeypatch.setenv("ECOORIGEM_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ECOORIGEM_DIFFICULTY", "2")
    monkeypatch.setenv("ECOORIGEM_DEMO_SEED", "tests")
    _, app = build_node(Settings.from_env())
    server = make_server("127.0.0.1", 0, app, threaded=True)
    url = f"http://127.0.0.1:{server.server_port}"
    monkeypatch.setenv("ECOORIGEM_NODE_URL", url)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield url
    server.shutdown()
    thread.join(timeout=5)


def test_client_reports_unavailable_node():
    client = NodeClient(http_transport("http://127.0.0.1:1", timeout=0.5))
    with pytest.raises(NodeUnavailableError):
        client.health()


def test_client_translates_remote_errors(live):
    client = NodeClient.from_url(live)
    with pytest.raises(RemoteRejectionError) as caught:
        client.request("GET", "/contract/lots/LOT-0001")
    assert caught.value.code == "CONTRACT_NOT_DEPLOYED"
    assert caught.value.http_status == 409
    assert caught.value.layer == "transaction"


def test_client_send_requires_deployment(live, tmp_path):
    keystore = Keystore.load_or_create(tmp_path / "wallet" / "wallets.json", "tests")
    with pytest.raises(ContractNotDeployedError):
        NodeClient.from_url(live).send(keystore.get("produtor"), "register_lot", {})


@pytest.mark.usefixtures("live")
def test_cli_full_journey(capsys):
    assert main(["accounts"]) == 0
    assert "administrador" in capsys.readouterr().out

    assert main(["deploy", "--wait", "5"]) == 0
    out = capsys.readouterr().out
    assert "Contrato implantado" in out and "Perfis concedidos" in out

    assert main(["deploy"]) == 0  # idempotent
    out = capsys.readouterr().out
    assert "já estava implantado" in out and "já estavam concedidos" in out

    assert main(["seed"]) == 0
    assert "LOT-0005" in capsys.readouterr().out

    assert main(["status"]) == 0
    assert '"deployed": true' in capsys.readouterr().out

    assert main(["validate"]) == 0
    assert "íntegra" in capsys.readouterr().out

    assert main(["chain", "--last", "2"]) == 0
    out = capsys.readouterr().out
    for field in ("Hash anterior", "Timestamp", "Dados", "Hash", "Nonce"):
        assert field in out
    assert out.count("BLOCO #") == 2
    assert "Blockchain é válida? Sim" in out

    assert main(["chain"]) == 0
    assert "BLOCO #0 (GÊNESIS)" in capsys.readouterr().out


def test_cli_validate_reports_tampering(live, capsys):
    assert main(["deploy", "--wait", "5", "--no-roles"]) == 0
    capsys.readouterr()
    client = NodeClient.from_url(live)
    keystore = Keystore.load_or_create(Settings.from_env().keystore_path, "tests")
    client.send(
        keystore.get("administrador"),
        "grant_role",
        {"account": keystore.get("produtor").address, "role": "PRODUCER"},
    )
    client.request(
        "POST",
        "/lab/tamper",
        payload={"block_index": 2, "changes": {"role": "CARRIER"}},
    )
    assert main(["validate"]) == 2
    out = capsys.readouterr().out
    assert "INVÁLIDA" in out and "MERKLE_MISMATCH" in out
    assert main(["chain", "--last", "1"]) == 2
    assert "Blockchain é válida? Não, a partir do bloco #2" in capsys.readouterr().out


def test_cli_reports_unreachable_node(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ECOORIGEM_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ECOORIGEM_NODE_URL", "http://127.0.0.1:1")
    assert main(["status"]) == 1
    assert "Erro:" in capsys.readouterr().out


def test_cli_reset_removes_local_data(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ECOORIGEM_DATA_DIR", str(tmp_path))
    (tmp_path / "node").mkdir()
    (tmp_path / "wallet").mkdir()
    assert main(["reset", "--yes"]) == 0
    assert not (tmp_path / "node").exists() and not (tmp_path / "wallet").exists()
    assert "removidos" in capsys.readouterr().out


def test_cli_reset_asks_for_confirmation(monkeypatch, tmp_path):
    monkeypatch.setenv("ECOORIGEM_DATA_DIR", str(tmp_path))
    (tmp_path / "node").mkdir()
    monkeypatch.setattr("builtins.input", lambda _prompt: "nao")
    assert main(["reset"]) == 1
    assert (tmp_path / "node").exists()


def test_parser_requires_a_command():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_settings_defaults_and_flags(monkeypatch):
    for name in ("ECOORIGEM_AUTO_MINE", "ECOORIGEM_LAB", "ECOORIGEM_DIFFICULTY"):
        monkeypatch.delenv(name, raising=False)
    settings = Settings.from_env()
    assert settings.difficulty == 4 and settings.auto_mine and settings.lab_enabled
    monkeypatch.setenv("ECOORIGEM_AUTO_MINE", "0")
    monkeypatch.setenv("ECOORIGEM_LAB", "nao")
    settings = Settings.from_env()
    assert not settings.auto_mine and not settings.lab_enabled


def test_wsgi_factories(monkeypatch, tmp_path):
    from ecoorigem import wsgi  # pylint: disable=import-outside-toplevel

    monkeypatch.setenv("ECOORIGEM_DATA_DIR", str(tmp_path))
    assert wsgi.node_app().test_client().get("/health").status_code == 200
    assert wsgi.web_app().test_client().get("/healthz").status_code == 200
    assert build_web(Settings.from_env()) is not None
