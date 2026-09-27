"""Tests for wallets, signatures and the keystore."""

import json
import stat

from ecoorigem.blockchain.wallet import (
    ADDRESS_PATTERN,
    Wallet,
    address_from_public_key,
    verify_signature,
)
from ecoorigem.keystore import DEMO_PROFILES, Keystore


def test_wallet_address_format_and_derivation():
    wallet = Wallet.generate("teste")
    assert ADDRESS_PATTERN.match(wallet.address)
    assert wallet.address == address_from_public_key(wallet.public_key)


def test_seeded_wallets_are_reproducible_and_distinct():
    assert Wallet.from_seed("a", "s").address == Wallet.from_seed("a", "s").address
    assert Wallet.from_seed("a", "s").address != Wallet.from_seed("b", "s").address


def test_signature_verifies_only_for_the_signed_message():
    wallet = Wallet.generate("teste")
    signature = wallet.sign(b"mensagem")
    assert verify_signature(wallet.public_key, b"mensagem", signature)
    assert not verify_signature(wallet.public_key, b"outra", signature)


def test_signature_from_another_key_is_rejected():
    signer, other = Wallet.generate("a"), Wallet.generate("b")
    signature = signer.sign(b"x")
    assert not verify_signature(other.public_key, b"x", signature)


def test_malformed_signature_inputs_are_rejected():
    wallet = Wallet.generate("teste")
    assert not verify_signature("zz", b"x", wallet.sign(b"x"))
    assert not verify_signature(wallet.public_key, b"x", "abc")


def test_private_key_export_roundtrip():
    wallet = Wallet.generate("teste")
    restored = Wallet("teste", wallet.export_private_key())
    assert restored.address == wallet.address
    assert "Wallet(" in repr(wallet)
    assert wallet.export_private_key() not in repr(wallet)


def test_keystore_creates_all_profiles_with_private_permissions(tmp_path):
    path = tmp_path / "wallet" / "wallets.json"
    keystore = Keystore.load_or_create(path)
    assert keystore.labels() == [profile.label for profile in DEMO_PROFILES]
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert len(set(w.address for w in keystore.wallets())) == len(DEMO_PROFILES)


def test_keystore_reloads_same_wallets(tmp_path):
    path = tmp_path / "wallets.json"
    first = Keystore.load_or_create(path)
    second = Keystore.load_or_create(path)
    assert [w.address for w in first.wallets()] == [w.address for w in second.wallets()]


def test_keystore_seed_is_reproducible(tmp_path):
    one = Keystore.load_or_create(tmp_path / "a.json", seed="demo")
    two = Keystore.load_or_create(tmp_path / "b.json", seed="demo")
    assert [w.address for w in one.wallets()] == [w.address for w in two.wallets()]


def test_keystore_lookup_by_label_and_address(tmp_path):
    keystore = Keystore.load_or_create(tmp_path / "w.json")
    wallet = keystore.get("produtor")
    assert wallet is not None
    assert keystore.get(wallet.address) is wallet
    assert keystore.get("inexistente") is None


def test_keystore_file_is_valid_json(tmp_path):
    path = tmp_path / "w.json"
    Keystore.load_or_create(path)
    assert "wallets" in json.loads(path.read_text(encoding="utf-8"))
