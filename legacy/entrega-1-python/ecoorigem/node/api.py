"""HTTP interface of the local blockchain node.

It plays the role of the JSON-RPC endpoint of an Ethereum client: applications
read the chain and submit already signed transactions through it. The node
never receives private keys.
"""

from __future__ import annotations

import re
from typing import Any

from flask import Flask, jsonify, request

from ecoorigem.errors import MalformedTransactionError
from ecoorigem.http_utils import error_response, register_error_handlers
from ecoorigem.node.ledger_node import LedgerNode

HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def create_node_app(node: LedgerNode) -> Flask:  # pylint: disable=too-many-locals
    """Build the Flask application that exposes ``node`` over HTTP."""
    app = Flask("ecoorigem-node")
    app.json.ensure_ascii = False  # type: ignore[attr-defined]
    app.json.sort_keys = False  # type: ignore[attr-defined]

    def body() -> dict[str, Any]:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            raise MalformedTransactionError(
                "O corpo da requisição deve ser um objeto JSON."
            )
        return payload

    def int_arg(name: str, default: int) -> int:
        try:
            return int(request.args.get(name, default))
        except ValueError:
            return default

    register_error_handlers(app)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/status")
    def status():
        return jsonify(node.status())

    @app.get("/blocks")
    def blocks():
        newest_first = request.args.get("order", "desc") != "asc"
        return jsonify(
            node.blocks(int_arg("offset", 0), int_arg("limit", 20), newest_first)
        )

    @app.get("/blocks/<int:index>")
    def block(index: int):
        found = node.block(index)
        if found is None:
            return error_response(
                "BLOCK_NOT_FOUND", f"O bloco {index} não existe.", 404
            )
        return jsonify(found)

    @app.post("/transactions")
    def submit_transaction():
        receipt = node.submit_transaction(request.get_json(silent=True))
        return jsonify(receipt), 201

    @app.get("/transactions/<tx_hash>")
    def transaction(tx_hash: str):
        found = node.transaction(tx_hash) if HASH_PATTERN.match(tx_hash) else None
        if found is None:
            return error_response("TX_NOT_FOUND", "Transação não encontrada.", 404)
        return jsonify(found)

    @app.get("/transactions/<tx_hash>/proof")
    def proof(tx_hash: str):
        found = node.inclusion_proof(tx_hash) if HASH_PATTERN.match(tx_hash) else None
        if found is None:
            return error_response(
                "TX_NOT_FOUND", "Transação confirmada não encontrada.", 404
            )
        return jsonify(found)

    @app.get("/accounts/<address>")
    def account(address: str):
        return jsonify(node.account(address))

    @app.get("/contract")
    def contract():
        summary = node.contract_summary()
        return jsonify({"deployed": summary is not None, "contract": summary})

    @app.get("/contract/lots")
    def lots():
        return jsonify({"lots": node.lots(request.args.get("status") or None)})

    @app.get("/contract/lots/<lot_id>")
    def lot(lot_id: str):
        return jsonify(node.lot(lot_id))

    @app.post("/contract/documents/verify")
    def verify_document():
        payload = body()
        return jsonify(
            node.verify_document(
                str(payload.get("lot_id", "")), str(payload.get("hash", ""))
            )
        )

    @app.get("/validate")
    def validate():
        return jsonify(node.validate().to_dict())

    @app.get("/rejections")
    def rejections():
        return jsonify({"rejections": node.rejections(int_arg("limit", 50))})

    @app.post("/mine")
    def mine():
        mined = node.mine_pending()
        return jsonify(
            {
                "mined": mined is not None,
                "block": node.block(mined.index) if mined else None,
            }
        )

    @app.post("/lab/tamper")
    def lab_tamper():
        payload = body()
        changes = payload.get("changes")
        block_index = payload.get("block_index")
        if not isinstance(changes, dict) or not isinstance(block_index, int):
            raise MalformedTransactionError("Informe 'block_index' e 'changes'.")
        report = node.lab_tamper(block_index, changes, bool(payload.get("remine")))
        return jsonify(report.to_dict())

    @app.post("/lab/restore")
    def lab_restore():
        return jsonify(node.lab_restore().to_dict())

    return app
