"""Tests for the HTTP API of the node."""

from __future__ import annotations

import pytest

from ecoorigem.node.api import create_node_app
from tests.conftest import DOC_HASH, VALID_LOT


@pytest.fixture(name="http")
def http_fixture(deployed):
    """Flask test client bound to a node with the contract deployed."""
    client = deployed()
    app = create_node_app(client.node)
    return app.test_client(), client


def test_health_and_status(http):
    web, _ = http
    assert web.get("/health").get_json() == {"status": "ok"}
    status = web.get("/status").get_json()
    assert status["contract"]["deployed"] is True
    assert status["integrity"]["valid"] is True


def test_submit_valid_transaction_returns_receipt(http, wallets):
    web, client = http
    tx = client.build(wallets["produtor"], "register_lot", VALID_LOT)
    response = web.post("/transactions", json=tx.to_dict())
    assert response.status_code == 201
    assert response.get_json()["status"] == "confirmed"


def test_contract_rejection_maps_to_http_status(http, wallets):
    web, client = http
    denied = client.build(wallets["intruso"], "register_lot", VALID_LOT)
    response = web.post("/transactions", json=denied.to_dict())
    body = response.get_json()
    assert response.status_code == 403
    assert body["status"] == "rejected"
    assert body["error"]["code"] == "ACCESS_DENIED"
    assert body["error"]["layer"] == "contract"


@pytest.mark.parametrize("payload", [None, [], {"type": "call"}])
def test_malformed_body_is_a_400(http, payload):
    web, _ = http
    response = web.post("/transactions", json=payload)
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "MALFORMED_TRANSACTION"


def test_invalid_json_body_is_a_400(http):
    web, _ = http
    response = web.post("/transactions", data="não é json", content_type="text/plain")
    assert response.status_code == 400


def test_lots_endpoints(http, wallets):
    web, client = http
    client.call(
        wallets["produtor"], "register_lot", {**VALID_LOT, "document_hash": DOC_HASH}
    )
    assert len(web.get("/contract/lots").get_json()["lots"]) == 1
    assert web.get("/contract/lots?status=FINALIZED").get_json()["lots"] == []
    assert web.get("/contract/lots/LOT-0001").get_json()["product"] == "Açaí"
    missing = web.get("/contract/lots/LOT-0099")
    assert missing.status_code == 404
    assert missing.get_json()["error"]["code"] == "LOT_NOT_FOUND"


def test_document_verification_endpoint(http, wallets):
    web, client = http
    client.call(
        wallets["produtor"], "register_lot", {**VALID_LOT, "document_hash": DOC_HASH}
    )
    ok = web.post(
        "/contract/documents/verify", json={"lot_id": "LOT-0001", "hash": DOC_HASH}
    )
    assert ok.get_json()["registered"] is True
    assert web.post("/contract/documents/verify", data="x").status_code == 400


def test_block_and_transaction_lookup(http, wallets):
    web, client = http
    receipt = client.call(wallets["produtor"], "register_lot", VALID_LOT)
    assert (
        web.get(f"/blocks/{receipt['block_index']}").get_json()["transaction_count"]
        == 1
    )
    assert web.get("/blocks/999").status_code == 404
    assert web.get(f"/transactions/{receipt['tx_hash']}").status_code == 200
    assert (
        web.get(f"/transactions/{receipt['tx_hash']}/proof").get_json()["valid"] is True
    )
    assert web.get("/transactions/xyz").status_code == 404
    assert web.get("/transactions/xyz/proof").status_code == 404


def test_blocks_pagination_parameters(http):
    web, _ = http
    page = web.get("/blocks?offset=1&limit=2&order=asc").get_json()
    assert [b["index"] for b in page["blocks"]] == [1, 2]
    fallback = web.get("/blocks?offset=abc&limit=zzz").get_json()
    assert fallback["offset"] == 0 and fallback["limit"] == 20


def test_account_contract_and_rejections(http, wallets):
    web, client = http
    account = web.get(f"/accounts/{wallets['produtor'].address}").get_json()
    assert account["roles"] == ["PRODUCER"]
    assert web.get("/contract").get_json()["deployed"] is True
    web.post(
        "/transactions",
        json=client.build(wallets["intruso"], "register_lot", VALID_LOT).to_dict(),
    )
    assert (
        web.get("/rejections?limit=5").get_json()["rejections"][0]["code"]
        == "ACCESS_DENIED"
    )


def test_mine_endpoint(http, wallets):
    web, client = http
    assert web.post("/mine").get_json()["mined"] is False
    client.node.auto_mine = False
    client.call(wallets["produtor"], "register_lot", VALID_LOT)
    mined = web.post("/mine").get_json()
    assert mined["mined"] is True and mined["block"]["transaction_count"] == 1


def test_lab_endpoints(http, wallets):
    web, client = http
    client.call(wallets["produtor"], "register_lot", VALID_LOT)
    block = client.node.status()["height"] - 1
    bad = web.post("/lab/tamper", json={"block_index": "x", "changes": {}})
    assert bad.status_code == 400
    report = web.post(
        "/lab/tamper", json={"block_index": block, "changes": {"quantity_kg": 1}}
    ).get_json()
    assert report["valid"] is False
    blocked = web.post(
        "/transactions",
        json=client.build(wallets["produtor"], "register_lot", VALID_LOT).to_dict(),
    )
    assert blocked.status_code == 423
    assert web.get("/validate").get_json()["valid"] is False
    assert web.post("/lab/restore").get_json()["valid"] is True


def test_unknown_route_returns_json_404(http):
    web, _ = http
    response = web.get("/nao-existe")
    assert response.status_code == 404
    assert response.get_json()["status"] == "error"
