"""Tests for hashing helpers and the Merkle tree."""

import pytest

from ecoorigem.blockchain.hashing import canonical_json, sha256_hex
from ecoorigem.blockchain.merkle import (
    EMPTY_ROOT,
    merkle_proof,
    merkle_root,
    verify_merkle_proof,
)


def test_sha256_known_vector():
    assert (
        sha256_hex("abc")
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_sha256_accepts_bytes_and_text_equally():
    assert sha256_hex("açaí") == sha256_hex("açaí".encode("utf-8"))


def test_canonical_json_is_order_independent():
    assert canonical_json({"b": 1, "a": [1, 2]}) == canonical_json(
        {"a": [1, 2], "b": 1}
    )
    assert canonical_json({"a": 1}) == '{"a":1}'


def test_empty_merkle_root():
    assert merkle_root([]) == EMPTY_ROOT


def test_single_leaf_root_is_the_leaf():
    leaf = sha256_hex("tx")
    assert merkle_root([leaf]) == leaf


def test_root_changes_when_any_leaf_changes():
    leaves = [sha256_hex(str(i)) for i in range(5)]
    root = merkle_root(leaves)
    altered = list(leaves)
    altered[3] = sha256_hex("changed")
    assert merkle_root(altered) != root


def test_root_depends_on_leaf_order():
    a, b = sha256_hex("a"), sha256_hex("b")
    assert merkle_root([a, b]) != merkle_root([b, a])


@pytest.mark.parametrize("size", [1, 2, 3, 4, 5, 8, 9])
def test_every_leaf_has_a_valid_proof(size):
    leaves = [sha256_hex(str(i)) for i in range(size)]
    root = merkle_root(leaves)
    for index, leaf in enumerate(leaves):
        assert verify_merkle_proof(leaf, merkle_proof(leaves, index), root)


def test_proof_fails_for_foreign_leaf():
    leaves = [sha256_hex(str(i)) for i in range(4)]
    proof = merkle_proof(leaves, 1)
    assert not verify_merkle_proof(sha256_hex("intruder"), proof, merkle_root(leaves))


def test_proof_index_out_of_range():
    with pytest.raises(IndexError):
        merkle_proof([sha256_hex("a")], 3)
