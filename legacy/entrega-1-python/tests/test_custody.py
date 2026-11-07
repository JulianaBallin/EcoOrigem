"""Focused tests for explicit custody handoff between supply-chain actors."""

from __future__ import annotations

import pytest

from ecoorigem.errors import AccessDeniedError
from tests.conftest import VALID_LOT


def test_default_products_exclude_handicrafts(deployed):
    client = deployed()
    assert client.node.contract is not None
    assert "Artesanato" not in client.node.contract.allowed_products


def test_only_designated_processor_can_process(deployed, wallets):
    client = deployed()

    client.call(
        wallets["administrador"],
        "grant_role",
        {"account": wallets["intruso"].address, "role": "PROCESSOR"},
    )

    client.call(
        wallets["produtor"],
        "register_lot",
        {
            **VALID_LOT,
            "processor": wallets["beneficiador"].address,
        },
    )

    with pytest.raises(AccessDeniedError):
        client.call(
            wallets["intruso"],
            "record_processing",
            {
                "lot_id": "LOT-0001",
                "description": "Tentativa indevida de beneficiamento",
                "carrier": wallets["transportador"].address,
            },
        )

    client.call(
        wallets["beneficiador"],
        "record_processing",
        {
            "lot_id": "LOT-0001",
            "description": "Beneficiamento autorizado",
            "carrier": wallets["transportador"].address,
        },
    )

    lot = client.node.lot("LOT-0001")
    assert lot["status"] == "PROCESSED"
    assert lot["processor"] == wallets["beneficiador"].address
    assert lot["carrier"] == wallets["transportador"].address


def test_only_designated_carrier_can_start_transport(deployed, wallets):
    client = deployed()

    client.call(
        wallets["administrador"],
        "grant_role",
        {"account": wallets["intruso"].address, "role": "CARRIER"},
    )

    client.call(
        wallets["produtor"],
        "register_lot",
        {
            **VALID_LOT,
            "processor": wallets["beneficiador"].address,
        },
    )
    client.call(
        wallets["beneficiador"],
        "record_processing",
        {
            "lot_id": "LOT-0001",
            "description": "Beneficiamento autorizado",
            "carrier": wallets["transportador"].address,
        },
    )

    with pytest.raises(AccessDeniedError):
        client.call(
            wallets["intruso"],
            "start_transport",
            {
                "lot_id": "LOT-0001",
                "recipient": wallets["distribuidor"].address,
                "destination": "Manaus",
            },
        )

    client.call(
        wallets["transportador"],
        "start_transport",
        {
            "lot_id": "LOT-0001",
            "recipient": wallets["distribuidor"].address,
            "destination": "Manaus",
        },
    )

    lot = client.node.lot("LOT-0001")
    assert lot["status"] == "IN_TRANSIT"
    assert lot["custodian"] == wallets["transportador"].address
