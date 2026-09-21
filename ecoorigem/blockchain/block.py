"""Blocks and proof of work."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ecoorigem.blockchain.hashing import canonical_json, sha256_hex
from ecoorigem.blockchain.merkle import merkle_root
from ecoorigem.blockchain.transaction import Transaction

GENESIS_PREVIOUS_HASH = "0" * 64


@dataclass
class Block:
    """A block: header, Merkle root of its transactions and the proof of work."""

    index: int
    timestamp: int
    previous_hash: str
    transactions: list[Transaction]
    difficulty: int
    note: str = ""
    nonce: int = 0
    merkle_root: str = ""
    hash: str = field(default="")

    def __post_init__(self) -> None:
        if not self.merkle_root:
            self.merkle_root = self.compute_merkle_root()
        if not self.hash:
            self.hash = self.compute_hash()

    def compute_merkle_root(self) -> str:
        """Recompute the Merkle root from the transactions."""
        return merkle_root([tx.hash for tx in self.transactions])

    def header(self) -> dict[str, Any]:
        """Return the fields covered by the block hash."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "difficulty": self.difficulty,
            "note": self.note,
            "nonce": self.nonce,
        }

    def compute_hash(self) -> str:
        """Compute the SHA-256 hash of the block header."""
        return sha256_hex(canonical_json(self.header()))

    def meets_difficulty(self) -> bool:
        """Check that the stored hash starts with ``difficulty`` zeros."""
        return self.hash.startswith("0" * self.difficulty)

    def mine(self) -> int:
        """Run the proof of work, incrementing the nonce until the hash is valid.

        Returns the number of attempts performed.
        """
        target = "0" * self.difficulty
        attempts = 1
        self.hash = self.compute_hash()
        while not self.hash.startswith(target):
            self.nonce += 1
            attempts += 1
            self.hash = self.compute_hash()
        return attempts

    def to_dict(self) -> dict[str, Any]:
        """Serialize the block."""
        return {
            **self.header(),
            "hash": self.hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Block":
        """Rebuild a block from stored data without recomputing its hash.

        The stored ``hash`` and ``merkle_root`` are preserved on purpose, so an
        altered file is detected by validation instead of being silently fixed.
        """
        return cls(
            index=raw["index"],
            timestamp=raw["timestamp"],
            previous_hash=raw["previous_hash"],
            transactions=[Transaction.from_dict(tx) for tx in raw["transactions"]],
            difficulty=raw["difficulty"],
            note=raw.get("note", ""),
            nonce=raw["nonce"],
            merkle_root=raw["merkle_root"],
            hash=raw["hash"],
        )

    @classmethod
    def genesis(cls, difficulty: int, timestamp: int, note: str) -> "Block":
        """Mine the genesis block, the first link of every chain."""
        block = cls(
            index=0,
            timestamp=timestamp,
            previous_hash=GENESIS_PREVIOUS_HASH,
            transactions=[],
            difficulty=difficulty,
            note=note,
        )
        block.mine()
        return block
