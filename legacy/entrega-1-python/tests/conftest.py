"""Shared fixtures: deterministic wallets, a controllable clock and nodes."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest

from ecoorigem.blockchain import TX_CALL, TX_DEPLOY, Transaction, Wallet
from ecoorigem.node import LedgerNode, LedgerStore

TEST_DIFFICULTY = 2
NOW_MS = 1_790_000_000_000  # fixed instant used by the fake clock (2026-09-21)


class FakeClock:
    """A clock that only moves when the test asks for it."""

    def __init__(self, start: int = NOW_MS) -> None:
        self.now = start

    def __call__(self) -> int:
        return self.now

    def advance(self, milliseconds: int) -> None:
        """Move the clock forward."""
        self.now += milliseconds


@pytest.fixture(name="clock")
def clock_fixture() -> FakeClock:
    """Return a fake clock."""
    return FakeClock()


@pytest.fixture(name="wallets")
def wallets_fixture() -> dict[str, Wallet]:
    """Return reproducible wallets for every demo profile."""
    labels = (
        "administrador",
        "produtor",
        "beneficiador",
        "transportador",
        "distribuidor",
        "intruso",
    )
    return {label: Wallet.from_seed(label, "tests") for label in labels}


@pytest.fixture(name="node")
def node_fixture(tmp_path: Path, clock: FakeClock) -> LedgerNode:
    """Return an empty node (no contract deployed yet)."""
    return LedgerNode(LedgerStore(tmp_path / "node"), TEST_DIFFICULTY, clock=clock)


class Client:
    """Helper that signs and submits transactions on behalf of wallets."""

    def __init__(self, node: LedgerNode, clock: FakeClock) -> None:
        self.node = node
        self.clock = clock

    def deploy(self, wallet: Wallet, args: dict[str, Any] | None = None) -> dict:
        """Deploy the contract from ``wallet``."""
        tx = Transaction.create(
            wallet,
            TX_DEPLOY,
            "EcoOrigem",
            args or {},
            self.node.account(wallet.address)["nonce"],
            timestamp=self.clock(),
        )
        return self.node.submit_transaction(tx.to_dict())

    def build(self, wallet: Wallet, method: str, args: dict[str, Any]) -> Transaction:
        """Build a signed call transaction without submitting it."""
        assert self.node.contract is not None
        return Transaction.create(
            wallet,
            TX_CALL,
            method,
            args,
            self.node.account(wallet.address)["nonce"],
            to=self.node.contract.address,
            timestamp=self.clock(),
        )

    def call(self, wallet: Wallet, method: str, args: dict[str, Any]) -> dict:
        """Sign and submit a contract call."""
        return self.node.submit_transaction(self.build(wallet, method, args).to_dict())


@pytest.fixture(name="client")
def client_fixture(node: LedgerNode, clock: FakeClock) -> Client:
    """Return a helper bound to the empty node."""
    return Client(node, clock)


@pytest.fixture(name="deployed")
def deployed_fixture(
    client: Client, wallets: dict[str, Wallet]
) -> Callable[[], Client]:
    """Deploy the contract and grant every role, returning the client."""

    def build() -> Client:
        client.deploy(wallets["administrador"])
        for label, role in ROLE_GRANTS.items():
            client.call(
                wallets["administrador"],
                "grant_role",
                {"account": wallets[label].address, "role": role},
            )
        return client

    return build


ROLE_GRANTS = {
    "produtor": "PRODUCER",
    "beneficiador": "PROCESSOR",
    "transportador": "CARRIER",
    "distribuidor": "DISTRIBUTOR",
}
VALID_LOT = {
    "product": "Açaí",
    "origin": "Maués, Amazonas",
    "quantity_kg": 250.5,
    "harvest_date": "2026-09-10",
}
DOC_HASH = "a" * 64


# --------------------------------------------------------------- HTTP helpers
def flask_transport(test_client):
    """Adapt a Flask test client to the transport expected by ``NodeClient``."""

    def send(method, path, params, payload):
        response = test_client.open(
            path, method=method, query_string=params, json=payload
        )
        return response.status_code, response.get_json()

    return send
