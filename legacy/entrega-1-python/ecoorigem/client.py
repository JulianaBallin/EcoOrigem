"""Client for the node HTTP API, including transaction signing helpers."""

from __future__ import annotations

from typing import Any, Callable, Protocol

import requests

from ecoorigem.blockchain.transaction import TX_CALL, TX_DEPLOY, Transaction
from ecoorigem.blockchain.wallet import Wallet
from ecoorigem.errors import ContractNotDeployedError, EcoOrigemError


class NodeUnavailableError(EcoOrigemError):
    """The node cannot be reached."""

    code = "NODE_UNAVAILABLE"
    layer = "client"
    http_status = 503


class RemoteRejectionError(EcoOrigemError):
    """The node rejected a request; carries the remote error description."""

    layer = "node"

    def __init__(self, status: int, error: dict[str, Any]) -> None:
        super().__init__(
            error.get("message", "Operação rejeitada pelo nó."), error.get("details")
        )
        self.code = error.get("code", "REMOTE_ERROR")
        self.layer = error.get("layer", "node")
        self.http_status = status


class Transport(Protocol):
    """Function that performs one HTTP exchange with the node."""

    def __call__(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None,
        payload: Any,
    ) -> tuple[int, Any]:
        """Return ``(status_code, decoded_json)``."""


def http_transport(base_url: str, timeout: float = 15.0) -> Transport:
    """Build a transport that talks to a node over HTTP."""

    def send(method: str, path: str, params: dict[str, Any] | None, payload: Any):
        try:
            response = requests.request(
                method,
                base_url.rstrip("/") + path,
                params=params,
                json=payload,
                timeout=timeout,
            )
        except requests.RequestException as error:
            raise NodeUnavailableError(
                "A blockchain local não respondeu. Verifique se o nó está em execução."
            ) from error
        try:
            return response.status_code, response.json()
        except ValueError:
            return response.status_code, {"error": {"message": response.text[:200]}}

    return send


class NodeClient:
    """Typed access to the node API."""

    def __init__(self, transport: Callable[..., tuple[int, Any]]) -> None:
        self._transport = transport

    @classmethod
    def from_url(cls, base_url: str) -> "NodeClient":
        """Create a client that reaches the node at ``base_url``."""
        return cls(http_transport(base_url))

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        payload: Any = None,
    ) -> Any:
        """Perform a request and raise :class:`RemoteRejectionError` on failure."""
        status, data = self._transport(method, path, params, payload)
        if status >= 400:
            error = data.get("error", {}) if isinstance(data, dict) else {}
            raise RemoteRejectionError(status, error)
        return data

    # ---------------------------------------------------------------- reads
    def health(self) -> dict[str, Any]:
        """Return the node health."""
        return self.request("GET", "/health")

    def status(self) -> dict[str, Any]:
        """Return the node overview."""
        return self.request("GET", "/status")

    def contract(self) -> dict[str, Any]:
        """Return the deployed contract description (or ``deployed: false``)."""
        return self.request("GET", "/contract")

    def account(self, address: str) -> dict[str, Any]:
        """Return nonce and roles of an account."""
        return self.request("GET", f"/accounts/{address}")

    # --------------------------------------------------------------- writes
    def submit(self, transaction: Transaction) -> dict[str, Any]:
        """Submit an already signed transaction."""
        return self.request("POST", "/transactions", payload=transaction.to_dict())

    def deploy(
        self, wallet: Wallet, args: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Sign and submit the contract deployment."""
        nonce = self.account(wallet.address)["nonce"]
        tx = Transaction.create(wallet, TX_DEPLOY, "EcoOrigem", args or {}, nonce)
        return self.submit(tx)

    def send(self, wallet: Wallet, method: str, args: dict[str, Any]) -> dict[str, Any]:
        """Sign and submit a call to the deployed contract."""
        info = self.contract()
        if not info["deployed"]:
            raise ContractNotDeployedError(
                "O contrato ainda não foi implantado. Execute a implantação primeiro."
            )
        nonce = self.account(wallet.address)["nonce"]
        tx = Transaction.create(
            wallet, TX_CALL, method, args, nonce, to=info["contract"]["address"]
        )
        return self.submit(tx)
