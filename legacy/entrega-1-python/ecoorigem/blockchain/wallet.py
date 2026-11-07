"""Wallets: Ed25519 key pairs, addresses and signature verification."""

from __future__ import annotations

import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from ecoorigem.blockchain.hashing import sha256_hex

ADDRESS_PATTERN = re.compile(r"^0x[0-9a-f]{40}$")
HEX_KEY_PATTERN = re.compile(r"^[0-9a-f]{64}$")
HEX_SIGNATURE_PATTERN = re.compile(r"^[0-9a-f]{128}$")


def address_from_public_key(public_key_hex: str) -> str:
    """Derive the account address (``0x`` + 40 hex chars) from a public key."""
    return "0x" + sha256_hex(bytes.fromhex(public_key_hex))[:40]


def verify_signature(public_key_hex: str, message: bytes, signature_hex: str) -> bool:
    """Return ``True`` when ``signature_hex`` signs ``message`` for the key."""
    if not HEX_KEY_PATTERN.match(public_key_hex):
        return False
    if not HEX_SIGNATURE_PATTERN.match(signature_hex):
        return False
    try:
        key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        key.verify(bytes.fromhex(signature_hex), message)
    except (InvalidSignature, ValueError):
        return False
    return True


class Wallet:
    """A local wallet able to sign transactions."""

    def __init__(self, label: str, private_key_hex: str) -> None:
        self.label = label
        self._private_key = Ed25519PrivateKey.from_private_bytes(
            bytes.fromhex(private_key_hex)
        )
        raw_public = self._private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        self.public_key = raw_public.hex()
        self.address = address_from_public_key(self.public_key)

    @classmethod
    def generate(cls, label: str) -> "Wallet":
        """Create a wallet with a fresh random private key."""
        private = Ed25519PrivateKey.generate()
        raw = private.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        )
        return cls(label, raw.hex())

    @classmethod
    def from_seed(cls, label: str, seed: str) -> "Wallet":
        """Derive a reproducible wallet from a text seed (development only)."""
        return cls(label, sha256_hex(f"{seed}:{label}"))

    def export_private_key(self) -> str:
        """Return the private key as hex. Handle with care."""
        raw = self._private_key.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        )
        return raw.hex()

    def sign(self, message: bytes) -> str:
        """Sign ``message`` and return the signature as hex."""
        return self._private_key.sign(message).hex()

    def __repr__(self) -> str:
        return f"Wallet(label={self.label!r}, address={self.address!r})"
