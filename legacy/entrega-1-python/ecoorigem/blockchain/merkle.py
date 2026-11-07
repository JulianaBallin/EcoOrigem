"""Merkle tree used to bind the transactions of a block to its header."""

from __future__ import annotations

from ecoorigem.blockchain.hashing import sha256_hex

EMPTY_ROOT = sha256_hex(b"")


def _next_level(level: list[str]) -> list[str]:
    """Hash adjacent pairs of nodes, duplicating the last one when odd."""
    padded = level + [level[-1]] if len(level) % 2 else level
    return [sha256_hex(padded[i] + padded[i + 1]) for i in range(0, len(padded), 2)]


def merkle_root(leaves: list[str]) -> str:
    """Compute the Merkle root of a list of transaction hashes."""
    if not leaves:
        return EMPTY_ROOT
    level = list(leaves)
    while len(level) > 1:
        level = _next_level(level)
    return level[0]


def merkle_proof(leaves: list[str], index: int) -> list[dict[str, str]]:
    """Build the inclusion proof of the leaf at ``index``.

    Each step gives the sibling hash and on which side it must be placed when
    recomputing the parent hash.
    """
    if not 0 <= index < len(leaves):
        raise IndexError("leaf index out of range")
    proof: list[dict[str, str]] = []
    level = list(leaves)
    position = index
    while len(level) > 1:
        padded = level + [level[-1]] if len(level) % 2 else level
        is_right = position % 2 == 1
        sibling = padded[position - 1] if is_right else padded[position + 1]
        proof.append({"hash": sibling, "side": "left" if is_right else "right"})
        level = _next_level(level)
        position //= 2
    return proof


def verify_merkle_proof(leaf: str, proof: list[dict[str, str]], root: str) -> bool:
    """Check that ``leaf`` belongs to the tree identified by ``root``."""
    current = leaf
    for step in proof:
        if step["side"] == "left":
            current = sha256_hex(step["hash"] + current)
        else:
            current = sha256_hex(current + step["hash"])
    return current == root
