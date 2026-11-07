"""Web application: serves the interface and signs transactions for the wallets.

The browser never talks to the node directly. It calls this gateway, which
plays the role of the wallet extension in a regular DApp: it keeps the private
keys of the demonstration accounts, signs the transaction of the selected
account and forwards it to the blockchain node.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

from ecoorigem import __version__
from ecoorigem.client import NodeClient
from ecoorigem.http_utils import error_response, register_error_handlers
from ecoorigem.errors import EcoOrigemError
from ecoorigem.keystore import PROFILE_BY_LABEL, Keystore
from ecoorigem.logs import get_logger

LOG = get_logger("web")

READ_ROUTES = [
    re.compile(pattern)
    for pattern in (
        r"^status$",
        r"^contract$",
        r"^contract/lots$",
        r"^contract/lots/[A-Za-z0-9_-]{1,32}$",
        r"^blocks$",
        r"^blocks/\d{1,9}$",
        r"^transactions/[0-9a-f]{64}$",
        r"^transactions/[0-9a-f]{64}/proof$",
        r"^validate$",
        r"^rejections$",
    )
]
WRITE_ROUTES = {
    "mine": re.compile(r"^mine$"),
    "contract/documents/verify": re.compile(r"^contract/documents/verify$"),
    "lab/tamper": re.compile(r"^lab/tamper$"),
    "lab/restore": re.compile(r"^lab/restore$"),
}


class WalletNotFoundError(EcoOrigemError):
    """The requested wallet does not exist in the keystore."""

    code = "WALLET_NOT_FOUND"
    layer = "wallet"
    http_status = 404


def assets_dir() -> Path:
    """Return the single folder that holds every static asset of the project."""
    configured = os.environ.get("ECOORIGEM_ASSETS_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "assets"


def create_web_app(client: NodeClient, keystore: Keystore) -> Flask:
    """Build the Flask application bound to a node client and a keystore."""
    app = Flask(__name__, static_folder=str(assets_dir()), static_url_path="/assets")
    app.json.ensure_ascii = False  # type: ignore[attr-defined]
    app.json.sort_keys = False  # type: ignore[attr-defined]

    register_error_handlers(app)

    @app.get("/")
    def index():
        return render_template("index.html", version=__version__)

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok", "wallets": len(keystore.labels())})

    @app.get("/api/wallets")
    def wallets():
        items: list[dict[str, Any]] = []
        for wallet in keystore.wallets():
            profile = PROFILE_BY_LABEL.get(wallet.label)
            info = client.account(wallet.address)
            items.append(
                {
                    "label": wallet.label,
                    "name": profile.display_name if profile else wallet.label.title(),
                    "description": profile.description if profile else "",
                    "address": wallet.address,
                    "nonce": info["nonce"],
                    "is_admin": info["is_admin"],
                    "roles": info["roles"],
                    "role_labels": info["role_labels"],
                }
            )
        return jsonify({"wallets": items})

    @app.post("/api/send")
    def send():
        payload = request.get_json(silent=True) or {}
        wallet = keystore.get(str(payload.get("wallet", "")))
        if wallet is None:
            raise WalletNotFoundError("Carteira não encontrada no keystore local.")
        args = payload.get("args")
        method = payload.get("method")
        if not isinstance(method, str) or not isinstance(args, dict):
            return error_response("BAD_REQUEST", "Informe 'method' e 'args'.", 400)
        LOG.info(
            "Carteira %s assinou %s e enviou ao nó.",
            wallet.label,
            method,
            extra={"tone": "info", "label": "ENVIO"},
        )
        try:
            receipt = client.send(wallet, method, args)
        except EcoOrigemError as error:
            LOG.warning(
                "%s de %s recusada: %s %s",
                method,
                wallet.label,
                error.code,
                error.message,
                extra={"tone": "bad", "label": "REJEITADA"},
            )
            raise
        LOG.info(
            "%s de %s confirmada no bloco #%s.",
            method,
            wallet.label,
            receipt.get("block_index"),
            extra={"tone": "ok", "label": "CONFIRMADA"},
        )
        return jsonify(receipt), 201

    @app.post("/api/deploy")
    def deploy():
        payload = request.get_json(silent=True) or {}
        wallet = keystore.get(str(payload.get("wallet", "administrador")))
        if wallet is None:
            raise WalletNotFoundError("Carteira não encontrada no keystore local.")
        return jsonify(client.deploy(wallet)), 201

    @app.get("/api/<path:path>")
    def read(path: str):
        if not any(route.match(path) for route in READ_ROUTES):
            return error_response("NOT_FOUND", "Rota inexistente.", 404)
        return jsonify(client.request("GET", "/" + path, params=dict(request.args)))

    @app.post("/api/<path:path>")
    def write(path: str):
        route = WRITE_ROUTES.get(path)
        if route is None:
            return error_response("NOT_FOUND", "Rota inexistente.", 404)
        return jsonify(
            client.request(
                "POST", "/" + path, payload=request.get_json(silent=True) or {}
            )
        )

    return app
