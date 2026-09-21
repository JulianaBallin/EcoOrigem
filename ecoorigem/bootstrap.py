"""Factories that assemble the node, the web application and the demo data."""

from __future__ import annotations

import time
from typing import Any

from flask import Flask

from ecoorigem.client import NodeClient, NodeUnavailableError
from ecoorigem.config import Settings
from ecoorigem.errors import EcoOrigemError
from ecoorigem.keystore import Keystore
from ecoorigem.node import LedgerNode, LedgerStore
from ecoorigem.node.api import create_node_app
from ecoorigem.web import create_web_app

DEMO_ROLES = {
    "produtor": "PRODUCER",
    "beneficiador": "PROCESSOR",
    "transportador": "CARRIER",
    "distribuidor": "DISTRIBUTOR",
}


def build_node(settings: Settings) -> tuple[LedgerNode, Flask]:
    """Create the ledger node and its HTTP application."""
    node = LedgerNode(
        LedgerStore(settings.node_dir),
        difficulty=settings.difficulty,
        auto_mine=settings.auto_mine,
        lab_enabled=settings.lab_enabled,
    )
    return node, create_node_app(node)


def build_web(settings: Settings) -> Flask:
    """Create the web application bound to the configured node."""
    keystore = Keystore.load_or_create(settings.keystore_path, settings.demo_seed)
    return create_web_app(NodeClient.from_url(settings.node_url), keystore)


def wait_for_node(client: NodeClient, seconds: float) -> None:
    """Block until the node answers or ``seconds`` elapse."""
    deadline = time.monotonic() + seconds
    while True:
        try:
            client.health()
            return
        except NodeUnavailableError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.5)


def deploy_contract(client: NodeClient, keystore: Keystore) -> dict[str, Any]:
    """Deploy the contract with the administrator wallet, if not deployed yet."""
    info = client.contract()
    if info["deployed"]:
        return {"deployed_now": False, "contract": info["contract"]}
    admin = keystore.get("administrador")
    if admin is None:
        raise EcoOrigemError("Carteira 'administrador' ausente no keystore.")
    receipt = client.deploy(admin)
    return {
        "deployed_now": True,
        "receipt": receipt,
        "contract": client.contract()["contract"],
    }


def grant_demo_roles(client: NodeClient, keystore: Keystore) -> list[str]:
    """Grant the business roles to the demo wallets. Returns what was granted."""
    admin = keystore.get("administrador")
    if admin is None:
        raise EcoOrigemError("Carteira 'administrador' ausente no keystore.")
    granted: list[str] = []
    for label, role in DEMO_ROLES.items():
        wallet = keystore.get(label)
        if wallet is None:
            continue
        if role in client.account(wallet.address)["roles"]:
            continue
        client.send(admin, "grant_role", {"account": wallet.address, "role": role})
        granted.append(f"{label}:{role}")
    return granted


def seed_demo_lots(client: NodeClient, keystore: Keystore) -> list[str]:
    """Create sample lots in different stages for demonstrations."""
    producer = _wallet(keystore, "produtor")
    processor = _wallet(keystore, "beneficiador")
    carrier = _wallet(keystore, "transportador")
    distributor = _wallet(keystore, "distribuidor")
    today = time.strftime("%Y-%m-%d", time.gmtime())
    samples = [
        ("Açaí", "Comunidade Ribeirinha do Rio Negro, Novo Airão", 420.0, 4),
        ("Castanha-do-Brasil", "Reserva Extrativista do Rio Cajari, Amapá", 1250.0, 3),
        ("Murumuru", "Assentamento Tupé, Manaus", 310.5, 2),
        ("Cupuaçu", "Cooperativa Agrícola de Presidente Figueiredo", 180.0, 1),
        ("Óleo vegetal", "Cooperativa de Andirobeiros de Maués", 96.0, 0),
    ]
    created: list[str] = []
    for product, origin, quantity, stage in samples:
        receipt = client.send(
            producer,
            "register_lot",
            {
                "product": product,
                "origin": origin,
                "quantity_kg": quantity,
                "harvest_date": today,
            },
        )
        lot_id = receipt["events"][0]["lot_id"]
        created.append(lot_id)
        if stage >= 1:
            client.send(
                processor,
                "record_processing",
                {
                    "lot_id": lot_id,
                    "description": f"Beneficiamento de {product.lower()} concluído.",
                },
            )
        if stage >= 2:
            client.send(
                carrier,
                "start_transport",
                {
                    "lot_id": lot_id,
                    "recipient": distributor.address,
                    "destination": "Centro de distribuição, Manaus",
                },
            )
        if stage >= 3:
            client.send(distributor, "confirm_delivery", {"lot_id": lot_id})
        if stage >= 4:
            client.send(
                distributor,
                "finalize_lot",
                {"lot_id": lot_id, "note": "Entrega ao varejo concluída."},
            )
    return created


def _wallet(keystore: Keystore, label: str):
    wallet = keystore.get(label)
    if wallet is None:
        raise EcoOrigemError(f"Carteira '{label}' ausente no keystore.")
    return wallet
