"""Tests for blocks, proof of work and chain validation."""

from dataclasses import replace

import pytest

from ecoorigem.blockchain import Blockchain, Transaction, TX_CALL, Wallet
from ecoorigem.blockchain.block import GENESIS_PREVIOUS_HASH, Block
from ecoorigem.errors import InvalidBlockError

DIFFICULTY = 2
CONTRACT = "0x" + "b" * 40


def make_tx(wallet: Wallet, nonce: int, value: str = "x") -> Transaction:
    """Build a signed call transaction."""
    return Transaction.create(
        wallet,
        TX_CALL,
        "register_lot",
        {"value": value},
        nonce,
        to=CONTRACT,
        timestamp=1_790_000_000_000 + nonce,
    )


@pytest.fixture(name="wallet")
def wallet_fixture() -> Wallet:
    """Reproducible producer wallet."""
    return Wallet.from_seed("produtor", "tests")


@pytest.fixture(name="chain")
def chain_fixture(wallet) -> Blockchain:
    """A chain with the genesis block and three mined blocks."""
    chain = Blockchain.create(DIFFICULTY, 1_790_000_000_000)
    for nonce in range(3):
        block, _ = chain.mine_block([make_tx(wallet, nonce)], 1_790_000_001_000 + nonce)
        chain.append(block)
    return chain


def test_genesis_block_properties():
    chain = Blockchain.create(DIFFICULTY, 1)
    genesis = chain.blocks[0]
    assert genesis.index == 0
    assert genesis.previous_hash == GENESIS_PREVIOUS_HASH
    assert genesis.hash.startswith("0" * DIFFICULTY)
    assert chain.validate().valid


def test_chain_requires_genesis():
    with pytest.raises(ValueError):
        Blockchain([])


def test_mining_finds_hash_with_required_prefix():
    block = Block(1, 1, "0" * 64, [], DIFFICULTY)
    attempts = block.mine()
    assert attempts >= 1
    assert block.hash.startswith("00")
    assert block.hash == block.compute_hash()


@pytest.mark.parametrize("difficulty", [1, 2, 3])
def test_difficulty_defines_required_hash_prefix(difficulty):
    block = Block(1, 1, "0" * 64, [], difficulty)
    block.mine()
    assert block.hash.startswith("0" * difficulty)
    assert block.meets_difficulty()


def test_valid_chain_passes_validation(chain):
    report = chain.validate()
    assert report.valid
    assert report.checked_blocks == 4
    assert report.first_invalid_block is None


def test_blocks_are_linked_by_hash(chain):
    for previous, current in zip(chain.blocks, chain.blocks[1:]):
        assert current.previous_hash == previous.hash


def test_append_rejects_wrong_link(chain, wallet):
    block, _ = chain.mine_block([make_tx(wallet, 3)], 1_790_000_009_000)
    block.previous_hash = "f" * 64
    with pytest.raises(InvalidBlockError):
        chain.append(block)


def test_append_rejects_wrong_index(chain, wallet):
    block, _ = chain.mine_block([make_tx(wallet, 3)], 1_790_000_009_000)
    block.index = 99
    with pytest.raises(InvalidBlockError):
        chain.append(block)


def test_append_rejects_stale_hash(chain, wallet):
    block, _ = chain.mine_block([make_tx(wallet, 3)], 1_790_000_009_000)
    block.note = "changed after mining"
    with pytest.raises(InvalidBlockError):
        chain.append(block)


def test_append_rejects_missing_proof_of_work(chain, wallet):
    block = Block(
        chain.tip.index + 1,
        1_790_000_009_000,
        chain.tip.hash,
        [make_tx(wallet, 3)],
        DIFFICULTY,
    )
    while block.hash.startswith("0" * DIFFICULTY):
        block.nonce += 1
        block.hash = block.compute_hash()
    with pytest.raises(InvalidBlockError):
        chain.append(block)


def test_append_rejects_wrong_merkle_root(chain, wallet):
    block, _ = chain.mine_block([make_tx(wallet, 3)], 1_790_000_009_000)
    block.merkle_root = "1" * 64
    block.hash = block.compute_hash()
    block.mine()
    with pytest.raises(InvalidBlockError):
        chain.append(block)


def test_timestamp_never_goes_backwards(chain, wallet):
    block, _ = chain.mine_block([make_tx(wallet, 3)], 1)
    assert block.timestamp == chain.tip.timestamp


def codes(chain: Blockchain) -> set[str]:
    """Return the issue codes reported by the validation."""
    return {issue.code for issue in chain.validate().issues}


def test_detects_transaction_data_change(chain):
    block = chain.blocks[2]
    block.transactions[0] = replace(block.transactions[0], args={"value": "forged"})
    report = chain.validate()
    assert not report.valid
    assert report.first_invalid_block == 2
    assert {"MERKLE_MISMATCH", "TX_SIGNATURE_INVALID"} <= codes(chain)


def test_detects_header_change(chain):
    chain.blocks[1].note = "forged"
    assert "HASH_MISMATCH" in codes(chain)


def test_detects_broken_link_after_rehash(chain):
    block = chain.blocks[1]
    block.note = "forged"
    block.mine()
    found = codes(chain)
    assert "BROKEN_LINK" in found
    assert chain.validate().first_invalid_block == 2


def test_detects_removed_block(chain):
    del chain.blocks[2]
    assert {"BAD_INDEX", "BROKEN_LINK"} <= codes(chain)


def test_detects_insufficient_proof_of_work(chain):
    block = chain.blocks[3]
    block.difficulty = 0
    block.hash = block.compute_hash()
    assert "POW_INVALID" in codes(chain)


def test_detects_altered_genesis(chain):
    chain.blocks[0].previous_hash = "1" * 64
    assert "GENESIS_INVALID" in codes(chain)


def test_detects_replayed_transaction_and_bad_nonce(chain):
    replay = chain.blocks[1].transactions[0]
    block, _ = chain.mine_block([replay], 1_790_000_009_000)
    chain.blocks.append(block)
    assert {"DUPLICATE_TX", "TX_NONCE_INVALID"} <= codes(chain)


def test_detects_timestamp_going_backwards(chain):
    chain.blocks[2].timestamp = chain.blocks[1].timestamp - 1
    chain.blocks[2].mine()
    assert "TIMESTAMP_ORDER" in codes(chain)


def test_serialization_roundtrip_preserves_validity(chain):
    restored = Blockchain.from_dict(chain.to_dict())
    assert restored.validate().valid
    assert [b.hash for b in restored.blocks] == [b.hash for b in chain.blocks]


def test_deserialization_keeps_tampered_hashes_so_it_is_detected(chain):
    data = chain.to_dict()
    data["blocks"][1]["transactions"][0]["args"] = {"value": "forged"}
    restored = Blockchain.from_dict(data)
    assert not restored.validate().valid


def test_report_serialization(chain):
    chain.blocks[1].note = "forged"
    payload = chain.validate().to_dict()
    assert payload["valid"] is False
    assert payload["issues"][0]["block_index"] == 1
