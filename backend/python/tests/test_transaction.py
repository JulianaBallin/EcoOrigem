"""Tests for signed transactions."""

from dataclasses import replace

import pytest

from ecoorigem.blockchain import TX_CALL, TX_DEPLOY, Transaction, Wallet
from ecoorigem.errors import InvalidSignatureError, MalformedTransactionError

CONTRACT = "0x" + "a" * 40


@pytest.fixture(name="wallet")
def wallet_fixture() -> Wallet:
    """Reproducible producer wallet."""
    return Wallet.from_seed("produtor", "tests")


def make_call(wallet: Wallet, **overrides) -> Transaction:
    """Build a signed call with optional field overrides."""
    params = {
        "tx_type": TX_CALL,
        "method": "register_lot",
        "args": {"product": "Açaí"},
        "nonce": 0,
        "to": CONTRACT,
        "timestamp": 1_790_000_000_000,
    }
    params.update(overrides)
    return Transaction.create(wallet, **params)


def test_created_transaction_verifies(wallet):
    make_call(wallet).verify()


def test_hash_is_deterministic_and_covers_arguments(wallet):
    first = make_call(wallet)
    assert first.hash == make_call(wallet).hash
    assert first.hash != make_call(wallet, args={"product": "Cupuaçu"}).hash


def test_tampered_arguments_invalidate_signature(wallet):
    tx = make_call(wallet)
    forged = replace(tx, args={"product": "Ouro"})
    with pytest.raises(InvalidSignatureError):
        forged.verify()


def test_sender_must_match_public_key(wallet):
    other = Wallet.from_seed("outro", "tests")
    tx = make_call(wallet)
    forged = replace(tx, sender=other.address)
    with pytest.raises(InvalidSignatureError):
        forged.verify()


def test_signature_from_another_wallet_is_rejected(wallet):
    other = Wallet.from_seed("outro", "tests")
    tx = make_call(wallet)
    forged = replace(tx, signature=make_call(other).signature)
    with pytest.raises(InvalidSignatureError):
        forged.verify()


def test_serialization_roundtrip_keeps_hash(wallet):
    tx = make_call(wallet)
    restored = Transaction.from_dict(tx.to_dict())
    assert restored == tx
    assert restored.hash == tx.hash


def test_hash_key_in_input_is_ignored(wallet):
    raw = make_call(wallet).to_dict()
    raw["hash"] = "0" * 64
    assert Transaction.from_dict(raw).hash != "0" * 64


def test_deploy_transaction_has_no_destination(wallet):
    tx = Transaction.create(wallet, TX_DEPLOY, "EcoOrigem", {}, 0)
    assert tx.to is None
    tx.verify()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d.pop("nonce"),
        lambda d: d.update(nonce="0"),
        lambda d: d.update(nonce=True),
        lambda d: d.update(nonce=-1),
        lambda d: d.update(args=[]),
        lambda d: d.update(type="transfer"),
        lambda d: d.update(sender="0x123"),
        lambda d: d.update(to="abc"),
        lambda d: d.update(to=None),
        lambda d: d.update(public_key="12"),
        lambda d: d.update(signature="12"),
        lambda d: d.update(method=""),
        lambda d: d.update(method="m" * 200),
        lambda d: d.update(args={"x": "y" * 20_000}),
        lambda d: d.update(args={"x": {1, 2}}),
    ],
)
def test_malformed_payloads_are_rejected(wallet, mutation):
    raw = make_call(wallet).to_dict()
    mutation(raw)
    with pytest.raises(MalformedTransactionError):
        Transaction.from_dict(raw)


def test_non_object_payload_is_rejected():
    with pytest.raises(MalformedTransactionError):
        Transaction.from_dict("texto")


def test_deploy_with_destination_is_rejected(wallet):
    raw = Transaction.create(wallet, TX_DEPLOY, "EcoOrigem", {}, 0).to_dict()
    raw["to"] = CONTRACT
    with pytest.raises(MalformedTransactionError):
        Transaction.from_dict(raw)
