"""Tests for the web gateway (wallet signing and read proxy)."""

from __future__ import annotations

import pytest

from ecoorigem.bootstrap import deploy_contract, grant_demo_roles, seed_demo_lots
from ecoorigem.client import NodeClient, NodeUnavailableError
from ecoorigem.keystore import Keystore
from ecoorigem.node import LedgerNode, LedgerStore
from ecoorigem.node.api import create_node_app
from ecoorigem.web import create_web_app
from tests.conftest import TEST_DIFFICULTY, flask_transport

LOT = {
    "product": "Açaí",
    "origin": "Maués, Amazonas",
    "quantity_kg": 100,
    "harvest_date": "2026-01-10",
}


@pytest.fixture(name="stack")
def stack_fixture(tmp_path):
    """Node, client, keystore and web app wired in-process."""
    node = LedgerNode(LedgerStore(tmp_path / "node"), TEST_DIFFICULTY)
    client = NodeClient(flask_transport(create_node_app(node).test_client()))
    keystore = Keystore.load_or_create(
        tmp_path / "wallet" / "wallets.json", seed="tests"
    )
    web = create_web_app(client, keystore).test_client()
    return node, client, keystore, web


@pytest.fixture(name="ready")
def ready_fixture(stack):
    """Stack with the contract deployed and the demo roles granted."""
    _, client, keystore, web = stack
    deploy_contract(client, keystore)
    grant_demo_roles(client, keystore)
    return client, keystore, web


def test_index_and_assets_are_served(stack):
    web = stack[3]
    page = web.get("/")
    assert page.status_code == 200 and "EcoOrigem" in page.get_data(as_text=True)
    assert "/assets/css/app.css" in page.get_data(as_text=True)
    for path in ("/assets/css/app.css", "/assets/js/app.js", "/assets/img/logo.png"):
        assert web.get(path).status_code == 200


def test_healthz(stack):
    assert stack[3].get("/healthz").get_json()["status"] == "ok"


def test_wallets_never_expose_private_keys(ready):
    _, keystore, web = ready
    response = web.get("/api/wallets")
    text = response.get_data(as_text=True)
    assert all(wallet.export_private_key() not in text for wallet in keystore.wallets())
    labels = {w["label"]: w for w in response.get_json()["wallets"]}
    assert labels["produtor"]["roles"] == ["PRODUCER"]
    assert labels["administrador"]["is_admin"] is True


def test_deploy_from_the_interface(stack):
    web = stack[3]
    assert web.post("/api/deploy", json={"wallet": "administrador"}).status_code == 201
    assert web.post("/api/deploy", json={"wallet": "administrador"}).status_code == 409
    assert web.post("/api/deploy", json={"wallet": "ninguem"}).status_code == 404


def test_send_signs_and_confirms(ready):
    _, _, web = ready
    response = web.post(
        "/api/send", json={"wallet": "produtor", "method": "register_lot", "args": LOT}
    )
    assert response.status_code == 201
    assert response.get_json()["events"][0]["name"] == "LOT_REGISTERED"
    assert web.get("/api/contract/lots/LOT-0001").get_json()["status"] == "REGISTERED"


def test_send_rejections_are_reported_with_reason(ready):
    _, _, web = ready
    denied = web.post(
        "/api/send", json={"wallet": "intruso", "method": "register_lot", "args": LOT}
    )
    assert denied.status_code == 403
    assert denied.get_json()["error"]["code"] == "ACCESS_DENIED"
    invalid = web.post(
        "/api/send",
        json={
            "wallet": "produtor",
            "method": "register_lot",
            "args": {**LOT, "quantity_kg": -1},
        },
    )
    assert invalid.status_code == 422
    assert invalid.get_json()["error"]["code"] == "INVALID_INPUT"
    assert (
        web.get("/api/rejections").get_json()["rejections"][0]["code"]
        == "INVALID_INPUT"
    )


def test_send_validates_request(ready):
    _, _, web = ready
    assert (
        web.post(
            "/api/send", json={"wallet": "ninguem", "method": "x", "args": {}}
        ).status_code
        == 404
    )
    assert web.post("/api/send", json={"wallet": "produtor"}).status_code == 400
    assert web.post("/api/send", data="x").status_code == 404


def test_send_before_deploy_is_rejected(stack):
    response = stack[3].post(
        "/api/send", json={"wallet": "produtor", "method": "register_lot", "args": LOT}
    )
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "CONTRACT_NOT_DEPLOYED"


@pytest.mark.parametrize(
    "path", ["nao-existe", "accounts/0x1", "lab/../status", "blocks/abc"]
)
def test_only_whitelisted_read_routes_are_proxied(ready, path):
    assert ready[2].get(f"/api/{path}").status_code == 404


@pytest.mark.parametrize("path", ["transactions", "lab/other", "send/extra"])
def test_only_whitelisted_write_routes_are_proxied(ready, path):
    assert ready[2].post(f"/api/{path}", json={}).status_code == 404


def test_write_proxy_routes(ready):
    _, _, web = ready
    web.post(
        "/api/send", json={"wallet": "produtor", "method": "register_lot", "args": LOT}
    )
    assert web.post("/api/mine").get_json()["mined"] is False
    assert (
        web.post(
            "/api/contract/documents/verify",
            json={"lot_id": "LOT-0001", "hash": "a" * 64},
        ).get_json()["registered"]
        is False
    )
    assert web.post("/api/lab/restore").get_json()["valid"] is True
    for path in ("status", "blocks?limit=2", "validate", "contract"):
        assert web.get(f"/api/{path}").status_code == 200


def test_node_offline_returns_503(tmp_path):
    def offline(*_args):
        raise NodeUnavailableError("A blockchain local não respondeu.")

    keystore = Keystore.load_or_create(tmp_path / "w.json", seed="tests")
    web = create_web_app(NodeClient(offline), keystore).test_client()
    for path in ("/api/status", "/api/wallets"):
        response = web.get(path)
        assert response.status_code == 503
        assert response.get_json()["error"]["code"] == "NODE_UNAVAILABLE"


def test_seed_creates_lots_in_every_stage(ready):
    client, keystore, _ = ready
    created = seed_demo_lots(client, keystore)
    statuses = [
        client.request("GET", f"/contract/lots/{lot}")["status"] for lot in created
    ]
    assert statuses == [
        "FINALIZED",
        "DISTRIBUTED",
        "IN_TRANSIT",
        "PROCESSED",
        "REGISTERED",
    ]
