"""Tests for the local blockchain node."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from ecoorigem.blockchain import TX_CALL, Transaction
from ecoorigem.errors import (
    AccessDeniedError,
    ChainCompromisedError,
    ContractAlreadyDeployedError,
    ContractNotDeployedError,
    ContractValidationError,
    DuplicateTransactionError,
    InvalidSignatureError,
    InvalidTransitionError,
    LotNotFoundError,
    MalformedTransactionError,
    NonceError,
    StaleTimestampError,
    TransactionError,
    WrongContractError,
)
from ecoorigem.node import LedgerNode, LedgerStore, StorageError
from tests.conftest import DOC_HASH, TEST_DIFFICULTY, VALID_LOT

# ------------------------------------------------------------------ deploy


def test_new_node_starts_with_a_valid_genesis_block(node):
    status = node.status()
    assert status["height"] == 1
    assert status["contract"]["deployed"] is False
    assert status["integrity"]["valid"] is True
    assert node.block(0)["hash"].startswith("0" * TEST_DIFFICULTY)


def test_deploy_creates_block_and_contract(client, node, wallets):
    receipt = client.deploy(wallets["administrador"])
    assert receipt["status"] == "confirmed"
    assert receipt["block_index"] == 1
    assert receipt["events"][0]["name"] == "CONTRACT_DEPLOYED"
    summary = node.contract_summary()
    assert summary["admin"] == wallets["administrador"].address
    assert summary["deployed_block"] == 1


def test_contract_cannot_be_deployed_twice(client, wallets):
    client.deploy(wallets["administrador"])
    with pytest.raises(ContractAlreadyDeployedError):
        client.deploy(wallets["intruso"])


def test_call_before_deploy_is_rejected(node, wallets):
    tx = Transaction.create(
        wallets["produtor"],
        TX_CALL,
        "register_lot",
        VALID_LOT,
        0,
        to="0x" + "c" * 40,
        timestamp=node.clock(),
    )
    with pytest.raises(ContractNotDeployedError):
        node.submit_transaction(tx.to_dict())


def test_call_to_wrong_contract_address_is_rejected(deployed, wallets):
    client = deployed()
    tx = Transaction.create(
        wallets["produtor"],
        TX_CALL,
        "register_lot",
        VALID_LOT,
        0,
        to="0x" + "d" * 40,
        timestamp=client.clock(),
    )
    with pytest.raises(WrongContractError):
        client.node.submit_transaction(tx.to_dict())


# -------------------------------------------------------- valid operations


def test_valid_operation_is_mined_into_a_block(deployed, wallets):
    client = deployed()
    height = client.node.status()["height"]
    receipt = client.call(wallets["produtor"], "register_lot", VALID_LOT)
    assert receipt["block_index"] == height
    assert client.node.status()["height"] == height + 1
    lot = client.node.lot("LOT-0001")
    assert lot["status"] == "REGISTERED"
    assert lot["history"][0]["block_index"] == height
    assert client.node.validate().valid


def test_nonce_advances_per_account(deployed, wallets):
    client = deployed()
    admin = wallets["administrador"].address
    assert client.node.account(admin)["nonce"] == 5  # deploy + 4 role grants
    assert client.node.account(admin)["is_admin"] is True
    assert client.node.account(wallets["produtor"].address)["roles"] == ["PRODUCER"]


def test_mined_block_meets_difficulty_and_links_to_previous(deployed, wallets):
    client = deployed()
    client.call(wallets["produtor"], "register_lot", VALID_LOT)
    tip = client.node.block(client.node.status()["height"] - 1)
    previous = client.node.block(tip["index"] - 1)
    assert tip["previous_hash"] == previous["hash"]
    assert tip["hash"].startswith("0" * TEST_DIFFICULTY)
    assert client.node.status()["last_mining"]["attempts"] >= 1


# -------------------------------------------------- invalid and rejected


def test_forged_signature_is_rejected_and_logged(deployed, wallets):
    client = deployed()
    tx = client.build(wallets["produtor"], "register_lot", VALID_LOT)
    forged = replace(tx, args={**VALID_LOT, "quantity_kg": 99999})
    with pytest.raises(InvalidSignatureError):
        client.node.submit_transaction(forged.to_dict())
    assert client.node.lots() == []
    assert client.node.rejections()[0]["code"] == "INVALID_SIGNATURE"


def test_transaction_signed_by_another_wallet_is_rejected(deployed, wallets):
    client = deployed()
    tx = client.build(wallets["produtor"], "register_lot", VALID_LOT)
    forged = replace(tx, sender=wallets["intruso"].address)
    with pytest.raises(InvalidSignatureError):
        client.node.submit_transaction(forged.to_dict())


def test_replayed_transaction_is_rejected(deployed, wallets):
    client = deployed()
    tx = client.build(wallets["produtor"], "register_lot", VALID_LOT)
    client.node.submit_transaction(tx.to_dict())
    with pytest.raises(DuplicateTransactionError):
        client.node.submit_transaction(tx.to_dict())
    assert len(client.node.lots()) == 1


def test_reused_nonce_with_new_content_is_rejected(deployed, wallets):
    client = deployed()
    stale = client.build(wallets["produtor"], "register_lot", VALID_LOT)
    client.call(
        wallets["produtor"], "register_lot", {**VALID_LOT, "origin": "Parintins"}
    )
    other = Transaction.create(
        wallets["produtor"],
        TX_CALL,
        "register_lot",
        {**VALID_LOT, "origin": "Coari, Amazonas"},
        stale.nonce,
        to=stale.to,
        timestamp=client.clock(),
    )
    with pytest.raises(NonceError):
        client.node.submit_transaction(other.to_dict())


def test_future_nonce_is_rejected(deployed, wallets):
    client = deployed()
    tx = Transaction.create(
        wallets["produtor"],
        TX_CALL,
        "register_lot",
        VALID_LOT,
        50,
        to=client.node.contract.address,
        timestamp=client.clock(),
    )
    with pytest.raises(NonceError):
        client.node.submit_transaction(tx.to_dict())


@pytest.mark.parametrize("offset", [-10 * 60 * 1000, 10 * 60 * 1000])
def test_timestamp_far_from_node_clock_is_rejected(deployed, wallets, offset):
    client = deployed()
    tx = Transaction.create(
        wallets["produtor"],
        TX_CALL,
        "register_lot",
        VALID_LOT,
        0,
        to=client.node.contract.address,
        timestamp=client.clock() + offset,
    )
    with pytest.raises(StaleTimestampError):
        client.node.submit_transaction(tx.to_dict())


@pytest.mark.parametrize("payload", [None, "texto", [], {}, {"type": "call"}])
def test_malformed_payloads_are_rejected_and_logged(node, payload):
    with pytest.raises(MalformedTransactionError):
        node.submit_transaction(payload)
    assert node.rejections()[0]["code"] == "MALFORMED_TRANSACTION"


def test_contract_rejections_are_logged_with_layer_and_sender(deployed, wallets):
    client = deployed()
    with pytest.raises(AccessDeniedError):
        client.call(wallets["intruso"], "register_lot", VALID_LOT)
    with pytest.raises(ContractValidationError):
        client.call(
            wallets["produtor"], "register_lot", {**VALID_LOT, "quantity_kg": -3}
        )
    with pytest.raises(LotNotFoundError):
        client.call(
            wallets["beneficiador"],
            "record_processing",
            {"lot_id": "LOT-0777", "description": "Lote inexistente"},
        )
    latest = client.node.rejections()
    assert [entry["code"] for entry in latest[:3]] == [
        "LOT_NOT_FOUND",
        "INVALID_INPUT",
        "ACCESS_DENIED",
    ]
    assert latest[2]["layer"] == "contract"
    assert latest[2]["sender"] == wallets["intruso"].address
    assert latest[2]["method"] == "register_lot"


def test_rejected_operation_does_not_create_a_block_or_consume_nonce(deployed, wallets):
    client = deployed()
    height = client.node.status()["height"]
    nonce = client.node.account(wallets["intruso"].address)["nonce"]
    with pytest.raises(AccessDeniedError):
        client.call(wallets["intruso"], "register_lot", VALID_LOT)
    assert client.node.status()["height"] == height
    assert client.node.account(wallets["intruso"].address)["nonce"] == nonce


def test_invalid_transition_is_rejected_through_the_node(deployed, wallets):
    client = deployed()
    client.call(wallets["produtor"], "register_lot", VALID_LOT)
    with pytest.raises(InvalidTransitionError):
        client.call(wallets["distribuidor"], "finalize_lot", {"lot_id": "LOT-0001"})
    assert client.node.lot("LOT-0001")["status"] == "REGISTERED"


def test_rejections_survive_restart(deployed, wallets, tmp_path, clock):
    client = deployed()
    with pytest.raises(AccessDeniedError):
        client.call(wallets["intruso"], "register_lot", VALID_LOT)
    reopened = LedgerNode(LedgerStore(tmp_path / "node"), clock=clock)
    assert reopened.rejections()[0]["code"] == "ACCESS_DENIED"
    assert reopened.status()["rejections"] == 1


# ------------------------------------------------------ mempool and mining


def test_manual_mining_batches_transactions_in_one_block(deployed, wallets):
    client = deployed()
    client.node.auto_mine = False
    height = client.node.status()["height"]
    first = client.call(wallets["produtor"], "register_lot", VALID_LOT)
    second = client.call(
        wallets["produtor"], "register_lot", {**VALID_LOT, "origin": "Coari"}
    )
    assert first["status"] == "pending"
    assert client.node.status()["pending"] == 2
    assert client.node.transaction(first["tx_hash"])["status"] == "pending"
    block = client.node.mine_pending()
    assert block.index == height and len(block.transactions) == 2
    assert client.node.status()["pending"] == 0
    assert client.node.mine_pending() is None
    proof = client.node.inclusion_proof(second["tx_hash"])
    assert proof["valid"] is True and proof["block_index"] == height
    assert client.node.validate().valid


def test_pending_transactions_see_previous_pending_state(deployed, wallets):
    client = deployed()
    client.node.auto_mine = False
    client.call(wallets["produtor"], "register_lot", VALID_LOT)
    client.call(
        wallets["beneficiador"],
        "record_processing",
        {"lot_id": "LOT-0001", "description": "Beneficiamento completo"},
    )
    client.node.mine_pending()
    assert client.node.lot("LOT-0001")["status"] == "PROCESSED"


def test_failed_disk_write_rolls_back_the_operation(deployed, wallets, monkeypatch):
    client = deployed()
    height = client.node.status()["height"]

    def broken(_data):
        raise OSError("disco cheio")

    monkeypatch.setattr(client.node.store, "save_chain", broken)
    with pytest.raises(OSError):
        client.call(wallets["produtor"], "register_lot", VALID_LOT)
    assert client.node.status()["height"] == height
    assert client.node.lots() == []
    assert client.node.status()["pending"] == 0


# ------------------------------------------------------------- persistence


def test_state_is_rebuilt_from_disk(deployed, wallets, tmp_path, clock):
    client = deployed()
    client.call(wallets["produtor"], "register_lot", VALID_LOT)
    reopened = LedgerNode(LedgerStore(tmp_path / "node"), clock=clock)
    assert reopened.status()["height"] == client.node.status()["height"]
    assert reopened.lot("LOT-0001")["origin"] == VALID_LOT["origin"]
    assert reopened.account(wallets["produtor"].address)["nonce"] == 1
    assert reopened.integrity_ok


def test_tampering_with_the_ledger_file_locks_the_node(
    deployed, wallets, tmp_path, clock
):
    client = deployed()
    client.call(wallets["produtor"], "register_lot", VALID_LOT)
    path = tmp_path / "node" / "ledger.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["blocks"][-1]["transactions"][0]["args"]["quantity_kg"] = 1
    path.write_text(json.dumps(data), encoding="utf-8")

    reopened = LedgerNode(LedgerStore(tmp_path / "node"), clock=clock)
    assert not reopened.integrity_ok
    assert (
        reopened.status()["integrity"]["first_invalid_block"] == len(data["blocks"]) - 1
    )
    tx = Transaction.create(
        wallets["produtor"],
        TX_CALL,
        "register_lot",
        VALID_LOT,
        reopened.account(wallets["produtor"].address)["nonce"],
        to=reopened.contract.address,
        timestamp=clock(),
    )
    with pytest.raises(ChainCompromisedError):
        reopened.submit_transaction(tx.to_dict())
    assert not reopened.lab_restore().valid  # the file itself is what changed


def test_unreadable_ledger_file_is_reported(tmp_path, clock):
    directory = tmp_path / "node"
    directory.mkdir()
    (directory / "ledger.json").write_text("{ isto não é json", encoding="utf-8")
    with pytest.raises(StorageError):
        LedgerNode(LedgerStore(directory), clock=clock)


def test_structurally_invalid_ledger_file_is_reported(tmp_path, clock):
    directory = tmp_path / "node"
    directory.mkdir()
    (directory / "ledger.json").write_text(
        '{"blocks": [{"index": 0}]}', encoding="utf-8"
    )
    with pytest.raises(TransactionError):
        LedgerNode(LedgerStore(directory), clock=clock)


def test_store_ignores_corrupted_rejection_lines(tmp_path):
    store = LedgerStore(tmp_path)
    store.append_rejection({"code": "X"})
    with store.rejections_path.open("a", encoding="utf-8") as handle:
        handle.write("linha quebrada\n\n")
    assert store.load_rejections() == [{"code": "X"}]


# ----------------------------------------------------- integrity laboratory


def test_laboratory_detects_tampering_and_restores(deployed, wallets):
    client = deployed()
    client.call(wallets["produtor"], "register_lot", VALID_LOT)
    block_index = client.node.status()["height"] - 1
    report = client.node.lab_tamper(block_index, {"quantity_kg": 99999})
    assert not report.valid and report.first_invalid_block == block_index
    assert not client.node.integrity_ok
    with pytest.raises(ChainCompromisedError):
        client.call(wallets["produtor"], "register_lot", VALID_LOT)
    assert client.node.lab_restore().valid
    client.call(wallets["produtor"], "register_lot", VALID_LOT)


def test_laboratory_rehash_is_caught_by_the_next_block(deployed, wallets):
    client = deployed()
    client.call(wallets["produtor"], "register_lot", VALID_LOT)
    client.call(wallets["produtor"], "register_lot", {**VALID_LOT, "origin": "Coari"})
    target = client.node.status()["height"] - 2
    report = client.node.lab_tamper(target, {"quantity_kg": 5}, remine=True)
    codes = {issue.code for issue in report.issues}
    assert "BROKEN_LINK" in codes and "TX_SIGNATURE_INVALID" in codes


def test_laboratory_input_validation(deployed):
    client = deployed()
    with pytest.raises(TransactionError):
        client.node.lab_tamper(0, {"a": 1})
    with pytest.raises(TransactionError):
        client.node.lab_tamper(99, {"a": 1})
    with pytest.raises(TransactionError):
        client.node.lab_tamper(1, {})
    client.node.lab_enabled = False
    with pytest.raises(TransactionError):
        client.node.lab_tamper(1, {"a": 1})


# ---------------------------------------------------------------- queries


def test_block_pagination_and_lookup(deployed):
    client = deployed()
    page = client.node.blocks(offset=0, limit=2)
    assert page["total"] == 6 and [b["index"] for b in page["blocks"]] == [5, 4]
    ascending = client.node.blocks(offset=0, limit=3, newest_first=False)
    assert [b["index"] for b in ascending["blocks"]] == [0, 1, 2]
    assert client.node.blocks(limit=9999)["limit"] == 200
    assert client.node.block(99) is None
    assert client.node.block(-1) is None


def test_transaction_lookup_includes_events_and_block(deployed, wallets):
    client = deployed()
    receipt = client.call(wallets["produtor"], "register_lot", VALID_LOT)
    found = client.node.transaction(receipt["tx_hash"])
    assert found["status"] == "confirmed"
    assert found["block_index"] == receipt["block_index"]
    assert found["events"][0]["name"] == "LOT_REGISTERED"
    assert client.node.transaction("0" * 64) is None
    assert client.node.inclusion_proof("0" * 64) is None


def test_document_verification(deployed, wallets):
    client = deployed()
    client.call(
        wallets["produtor"], "register_lot", {**VALID_LOT, "document_hash": DOC_HASH}
    )
    assert client.node.verify_document("LOT-0001", DOC_HASH)["registered"] is True
    assert client.node.verify_document("LOT-0001", "b" * 64)["registered"] is False
    with pytest.raises(LotNotFoundError):
        client.node.verify_document("LOT-0042", DOC_HASH)


def test_views_without_contract(node):
    assert node.lots() == []
    assert node.contract_summary() is None
    assert node.account("0x" + "1" * 40)["roles"] == []
    with pytest.raises(ContractNotDeployedError):
        node.lot("LOT-0001")
    with pytest.raises(ContractNotDeployedError):
        node.verify_document("LOT-0001", DOC_HASH)


def test_rejections_limit_and_order(deployed, wallets):
    client = deployed()
    for _ in range(3):
        with pytest.raises(AccessDeniedError):
            client.call(wallets["intruso"], "register_lot", VALID_LOT)
    assert len(client.node.rejections(limit=2)) == 2
