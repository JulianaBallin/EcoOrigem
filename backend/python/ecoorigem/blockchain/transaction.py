"""Signed transactions.

A transaction is the only way to change the state of the chain. It names the
sender, the contract method being called and its arguments, and it is signed
with the private key of the sender (Ed25519). The transaction hash covers every
field except the signature, so any modification invalidates both.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, replace
from typing import Any

from ecoorigem.blockchain.hashing import canonical_json, sha256_hex
from ecoorigem.blockchain.wallet import (
    ADDRESS_PATTERN,
    HEX_KEY_PATTERN,
    HEX_SIGNATURE_PATTERN,
    Wallet,
    address_from_public_key,
    verify_signature,
)
from ecoorigem.errors import InvalidSignatureError, MalformedTransactionError

TX_DEPLOY = "deploy"
TX_CALL = "call"
TX_TYPES = (TX_DEPLOY, TX_CALL)
MAX_ARGS_BYTES = 8 * 1024
MAX_METHOD_LENGTH = 64


def now_ms() -> int:
    """Return the current UTC time in milliseconds."""
    return int(time.time() * 1000)


@dataclass(frozen=True)
class Transaction:
    """An immutable, signed request to deploy or call the smart contract."""

    tx_type: str
    sender: str
    public_key: str
    nonce: int
    timestamp: int
    to: str | None
    method: str
    args: dict[str, Any] = field(default_factory=dict)
    signature: str = ""

    # ------------------------------------------------------------------
    # Hashing and signing
    # ------------------------------------------------------------------
    def payload(self) -> dict[str, Any]:
        """Return the signed content (everything except the signature)."""
        return {
            "type": self.tx_type,
            "sender": self.sender,
            "public_key": self.public_key,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "to": self.to,
            "method": self.method,
            "args": self.args,
        }

    @property
    def hash(self) -> str:
        """Return the transaction hash."""
        return sha256_hex(canonical_json(self.payload()))

    @classmethod
    def create(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        cls,
        wallet: Wallet,
        tx_type: str,
        method: str,
        args: dict[str, Any],
        nonce: int,
        to: str | None = None,
        timestamp: int | None = None,
    ) -> "Transaction":
        """Build and sign a transaction with ``wallet``."""
        unsigned = cls(
            tx_type=tx_type,
            sender=wallet.address,
            public_key=wallet.public_key,
            nonce=nonce,
            timestamp=now_ms() if timestamp is None else timestamp,
            to=to,
            method=method,
            args=args,
        )
        signature = wallet.sign(bytes.fromhex(unsigned.hash))
        return replace(unsigned, signature=signature)

    def verify(self) -> None:
        """Validate the sender address and the signature.

        Raises:
            InvalidSignatureError: if the address does not belong to the
                public key or the signature does not match the hash.
        """
        if address_from_public_key(self.public_key) != self.sender:
            raise InvalidSignatureError(
                "O endereço do remetente não corresponde à chave pública."
            )
        if not verify_signature(
            self.public_key, bytes.fromhex(self.hash), self.signature
        ):
            raise InvalidSignatureError("Assinatura digital inválida para a transação.")

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """Serialize the transaction, including its hash, for storage and API."""
        return {**self.payload(), "signature": self.signature, "hash": self.hash}

    @classmethod
    def from_dict(cls, raw: Any) -> "Transaction":
        """Parse untrusted input into a transaction, validating every field.

        The ``hash`` key, when present, is ignored: it is always recomputed.

        Raises:
            MalformedTransactionError: if a field is missing or has a bad type.
        """
        if not isinstance(raw, dict):
            raise MalformedTransactionError("A transação deve ser um objeto JSON.")
        tx_type = _require(raw, "type", str)
        if tx_type not in TX_TYPES:
            raise MalformedTransactionError(
                f"Tipo de transação desconhecido: {tx_type}."
            )
        sender = _require(raw, "sender", str)
        public_key = _require(raw, "public_key", str)
        signature = _require(raw, "signature", str)
        method = _require(raw, "method", str)
        nonce = _require(raw, "nonce", int)
        timestamp = _require(raw, "timestamp", int)
        args = _require(raw, "args", dict)
        to = raw.get("to")
        if to is not None and (
            not isinstance(to, str) or not ADDRESS_PATTERN.match(to)
        ):
            raise MalformedTransactionError("O campo 'to' deve ser um endereço válido.")
        if not ADDRESS_PATTERN.match(sender):
            raise MalformedTransactionError(
                "O campo 'sender' deve ser um endereço válido."
            )
        if not HEX_KEY_PATTERN.match(public_key):
            raise MalformedTransactionError("Chave pública em formato inválido.")
        if signature and not HEX_SIGNATURE_PATTERN.match(signature):
            raise MalformedTransactionError("Assinatura em formato inválido.")
        if nonce < 0 or timestamp < 0:
            raise MalformedTransactionError(
                "Nonce e timestamp não podem ser negativos."
            )
        if not method or len(method) > MAX_METHOD_LENGTH:
            raise MalformedTransactionError("Nome de método inválido.")
        if (tx_type == TX_DEPLOY) != (to is None):
            raise MalformedTransactionError(
                "Implantações não têm destino; chamadas exigem o endereço do contrato."
            )
        try:
            args_size = len(canonical_json(args).encode("utf-8"))
        except (TypeError, ValueError) as error:
            raise MalformedTransactionError("Argumentos não serializáveis.") from error
        if args_size > MAX_ARGS_BYTES:
            raise MalformedTransactionError("Argumentos excedem o tamanho máximo.")
        return cls(
            tx_type=tx_type,
            sender=sender,
            public_key=public_key,
            nonce=nonce,
            timestamp=timestamp,
            to=to,
            method=method,
            args=args,
            signature=signature,
        )


def _require(raw: dict[str, Any], key: str, expected: type) -> Any:
    """Return ``raw[key]`` ensuring the expected type (booleans are not ints)."""
    if key not in raw:
        raise MalformedTransactionError(f"Campo obrigatório ausente: {key}.")
    value = raw[key]
    if not isinstance(value, expected) or (expected is int and isinstance(value, bool)):
        raise MalformedTransactionError(f"Tipo inválido para o campo '{key}'.")
    return value
