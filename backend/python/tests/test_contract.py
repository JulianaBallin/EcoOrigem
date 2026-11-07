"""Tests for the business rules of the EcoOrigem smart contract."""

from __future__ import annotations

import pytest

from ecoorigem.blockchain import Wallet
from ecoorigem.contract import (
    CallContext,
    EcoOrigemContract,
    LotStatus,
    Role,
    contract_address,
)
from ecoorigem.errors import (
    AccessDeniedError,
    ContractValidationError,
    InvalidTransitionError,
    LotFinalizedError,
    LotNotFoundError,
    UnknownMethodError,
)
from tests.conftest import DOC_HASH, NOW_MS, ROLE_GRANTS, VALID_LOT


class Harness:
    """Runs contract methods as different wallets with an increasing tx hash."""

    def __init__(self, wallets: dict[str, Wallet]) -> None:
        self.wallets = wallets
        admin = wallets["administrador"]
        ctx = CallContext(
            admin.address, NOW_MS, "0" * 64, contract_address(admin.address, 0)
        )
        self.contract = EcoOrigemContract.deploy(ctx, {})
        self._counter = 0

    def run(self, who: str, method: str, args: dict, timestamp: int = NOW_MS):
        """Execute ``method`` as the wallet ``who``."""
        self._counter += 1
        ctx = CallContext(
            self.wallets[who].address,
            timestamp,
            f"{self._counter:064x}",
            self.contract.address,
        )
        return self.contract.execute(ctx, method, args)

    def grant_all(self) -> None:
        """Grant every business role to its demo wallet."""
        for label, role in ROLE_GRANTS.items():
            self.run(
                "administrador",
                "grant_role",
                {"account": self.wallets[label].address, "role": role},
            )

    def register(self, **overrides) -> str:
        """Register a valid lot (with optional overrides) and return its id."""
        self.run("produtor", "register_lot", {**VALID_LOT, **overrides})
        return (
            f"LOT-{self.contract._lot_counter:04d}"  # pylint: disable=protected-access
        )

    def advance_to(self, lot_id: str, target: str) -> None:
        """Walk the lot through the valid path up to ``target``."""
        for stage in STAGE_ORDER:
            self.run(*stage_call(self.wallets, lot_id, stage))
            if stage == target:
                return


STAGE_ORDER = ["PROCESSED", "IN_TRANSIT", "DISTRIBUTED", "FINALIZED"]


def stage_call(wallets: dict[str, Wallet], lot_id: str, stage: str):
    """Return (who, method, args) of the valid call that reaches ``stage``."""
    return {
        "PROCESSED": (
            "beneficiador",
            "record_processing",
            {"lot_id": lot_id, "description": "Despolpamento e congelamento"},
        ),
        "IN_TRANSIT": (
            "transportador",
            "start_transport",
            {
                "lot_id": lot_id,
                "recipient": wallets["distribuidor"].address,
                "destination": "Centro de distribuição, Manaus",
            },
        ),
        "DISTRIBUTED": ("distribuidor", "confirm_delivery", {"lot_id": lot_id}),
        "FINALIZED": ("distribuidor", "finalize_lot", {"lot_id": lot_id}),
    }[stage]


@pytest.fixture(name="harness")
def harness_fixture(wallets) -> Harness:
    """Contract deployed with every role granted."""
    harness = Harness(wallets)
    harness.grant_all()
    return harness


# ---------------------------------------------------------------- deployment
def test_deployer_becomes_admin_and_defaults_are_set(wallets):
    harness = Harness(wallets)
    summary = harness.contract.summary()
    assert summary["admin"] == wallets["administrador"].address
    assert "Açaí" in summary["allowed_products"]
    assert summary["lot_count"] == 0


def test_deploy_accepts_custom_product_list(wallets):
    admin = wallets["administrador"]
    ctx = CallContext(
        admin.address, NOW_MS, "1" * 64, contract_address(admin.address, 0)
    )
    contract = EcoOrigemContract.deploy(ctx, {"allowed_products": ["Babaçu", "Tucumã"]})
    assert contract.allowed_products == ("Babaçu", "Tucumã")


@pytest.mark.parametrize(
    "products", [[], "acai", ["a"], ["Açaí", "acai"], ["x" * 60], [1]]
)
def test_deploy_rejects_invalid_product_list(wallets, products):
    admin = wallets["administrador"]
    ctx = CallContext(
        admin.address, NOW_MS, "1" * 64, contract_address(admin.address, 0)
    )
    with pytest.raises(ContractValidationError):
        EcoOrigemContract.deploy(ctx, {"allowed_products": products})


def test_contract_address_depends_on_deployer_and_nonce():
    assert contract_address("0x" + "1" * 40, 0) != contract_address("0x" + "1" * 40, 1)
    assert contract_address("0x" + "1" * 40, 0) != contract_address("0x" + "2" * 40, 0)


def test_unknown_method_is_rejected(harness):
    with pytest.raises(UnknownMethodError):
        harness.run("administrador", "selfdestruct", {})


# ------------------------------------------------------------- role handling
def test_admin_grants_and_revokes_roles(harness, wallets):
    intruder = wallets["intruso"].address
    harness.run("administrador", "grant_role", {"account": intruder, "role": "CARRIER"})
    assert harness.contract.roles_of(intruder) == [Role.CARRIER]
    harness.run(
        "administrador", "revoke_role", {"account": intruder, "role": "CARRIER"}
    )
    assert harness.contract.roles_of(intruder) == []


@pytest.mark.parametrize("method", ["grant_role", "revoke_role"])
def test_only_admin_can_manage_roles(harness, wallets, method):
    with pytest.raises(AccessDeniedError):
        harness.run(
            "produtor",
            method,
            {"account": wallets["intruso"].address, "role": "PRODUCER"},
        )


def test_duplicate_grant_and_missing_revoke_are_rejected(harness, wallets):
    producer = wallets["produtor"].address
    with pytest.raises(ContractValidationError):
        harness.run(
            "administrador", "grant_role", {"account": producer, "role": "PRODUCER"}
        )
    with pytest.raises(ContractValidationError):
        harness.run(
            "administrador",
            "revoke_role",
            {"account": wallets["intruso"].address, "role": "PRODUCER"},
        )


@pytest.mark.parametrize(
    "args",
    [
        {"account": "0x1", "role": "PRODUCER"},
        {"account": "0x" + "1" * 40, "role": "KING"},
        {"account": "0x" + "1" * 40},
        {"account": "0x" + "1" * 40, "role": "PRODUCER", "extra": 1},
    ],
)
def test_grant_role_validates_arguments(harness, args):
    with pytest.raises(ContractValidationError):
        harness.run("administrador", "grant_role", args)


# ------------------------------------------------------------- lot creation
def test_producer_registers_lot(harness, wallets):
    events = harness.run(
        "produtor", "register_lot", {**VALID_LOT, "document_hash": DOC_HASH}
    )
    lot = harness.contract.get_lot("LOT-0001")
    assert lot.status is LotStatus.REGISTERED
    assert lot.producer == lot.custodian == wallets["produtor"].address
    assert lot.documents[0]["hash"] == DOC_HASH
    assert [event.name for event in events] == ["LOT_REGISTERED"]


def test_lot_ids_are_sequential(harness):
    assert [harness.register() for _ in range(3)] == [
        "LOT-0001",
        "LOT-0002",
        "LOT-0003",
    ]


def test_product_matching_ignores_case_and_accents(harness):
    harness.register(product="  ACAI ")
    assert harness.contract.get_lot("LOT-0001").product == "Açaí"


@pytest.mark.parametrize(
    "who", ["intruso", "beneficiador", "transportador", "distribuidor", "administrador"]
)
def test_only_producers_can_register_lots(harness, who):
    with pytest.raises(AccessDeniedError):
        harness.run(who, "register_lot", VALID_LOT)
    assert harness.contract.lots == {}


@pytest.mark.parametrize(
    "overrides",
    [
        {"product": "Diamante"},
        {"product": 7},
        {"origin": ""},
        {"origin": "ab"},
        {"origin": "x" * 200},
        {"origin": "linha\tcom tab"},
        {"quantity_kg": 0},
        {"quantity_kg": -5},
        {"quantity_kg": "10"},
        {"quantity_kg": True},
        {"quantity_kg": float("inf")},
        {"quantity_kg": float("nan")},
        {"quantity_kg": 100_000.5},
        {"harvest_date": "2999-01-01"},
        {"harvest_date": "10/09/2026"},
        {"harvest_date": "2026-02-30"},
        {"harvest_date": "1999-12-31"},
        {"harvest_date": 20260910},
        {"document_hash": "xyz"},
        {"document_hash": "a" * 63},
    ],
)
def test_register_lot_rejects_invalid_input(harness, overrides):
    with pytest.raises(ContractValidationError):
        harness.run("produtor", "register_lot", {**VALID_LOT, **overrides})
    assert harness.contract.lots == {}


def test_register_lot_rejects_missing_and_unknown_fields(harness):
    with pytest.raises(ContractValidationError):
        harness.run("produtor", "register_lot", {"product": "Açaí"})
    with pytest.raises(ContractValidationError):
        harness.run("produtor", "register_lot", {**VALID_LOT, "price": 1})


def test_optional_empty_values_are_ignored(harness):
    harness.register(document_hash="")
    assert harness.contract.get_lot("LOT-0001").documents == []


def test_harvest_date_uses_the_transaction_date(harness):
    with pytest.raises(ContractValidationError):
        harness.run(
            "produtor", "register_lot", {**VALID_LOT, "harvest_date": "2026-09-22"}
        )
    harness.run("produtor", "register_lot", {**VALID_LOT, "harvest_date": "2026-09-21"})


# ---------------------------------------------------------- valid life cycle
def test_full_life_cycle_updates_state_and_custody(harness, wallets):
    lot_id = harness.register()
    lot = harness.contract.get_lot(lot_id)
    holders = {
        "PROCESSED": "beneficiador",
        "IN_TRANSIT": "transportador",
        "DISTRIBUTED": "distribuidor",
        "FINALIZED": "distribuidor",
    }
    for stage in STAGE_ORDER:
        harness.run(*stage_call(wallets, lot_id, stage))
        assert lot.status.value == stage
        assert lot.custodian == wallets[holders[stage]].address
    assert [event.name for event in lot.history] == [
        "LOT_REGISTERED",
        "LOT_PROCESSED",
        "TRANSPORT_STARTED",
        "DELIVERY_CONFIRMED",
        "LOT_FINALIZED",
    ]
    assert lot.recipient == wallets["distribuidor"].address


def test_history_events_reference_actor_and_transition(harness, wallets):
    lot_id = harness.register()
    harness.advance_to(lot_id, "PROCESSED")
    event = harness.contract.get_lot(lot_id).history[-1]
    assert event.actor == wallets["beneficiador"].address
    assert (event.from_status, event.to_status) == ("REGISTERED", "PROCESSED")


# --------------------------------------------------------- invalid transitions
STAGE_ARGS = {
    "record_processing": ("beneficiador", {"description": "Beneficiamento completo"}),
    "start_transport": ("transportador", {"destination": "Manaus"}),
    "confirm_delivery": ("distribuidor", {}),
    "finalize_lot": ("distribuidor", {}),
}
NEXT_OF = {
    "REGISTERED": "record_processing",
    "PROCESSED": "start_transport",
    "IN_TRANSIT": "confirm_delivery",
    "DISTRIBUTED": "finalize_lot",
}


OUT_OF_ORDER = [
    (current, attempt)
    for current, valid_attempt in NEXT_OF.items()
    for attempt in STAGE_ARGS
    if attempt != valid_attempt
]


@pytest.mark.parametrize("current, attempt", OUT_OF_ORDER)
def test_stages_must_follow_the_mandatory_order(harness, wallets, current, attempt):
    lot_id = harness.register()
    if current != "REGISTERED":
        harness.advance_to(lot_id, current)
    who, extra = STAGE_ARGS[attempt]
    args = {"lot_id": lot_id, **extra}
    if attempt == "start_transport":
        args["recipient"] = wallets["distribuidor"].address
    with pytest.raises(InvalidTransitionError) as caught:
        harness.run(who, attempt, args)
    assert "próxima etapa" in caught.value.message
    assert harness.contract.get_lot(lot_id).status.value == current


def test_cannot_jump_from_registered_to_finalized(harness):
    lot_id = harness.register()
    with pytest.raises(InvalidTransitionError) as caught:
        harness.run("distribuidor", "finalize_lot", {"lot_id": lot_id})
    assert "CADASTRADO" in caught.value.message and "FINALIZADO" in caught.value.message


def test_stage_cannot_be_repeated(harness):
    lot_id = harness.register()
    harness.advance_to(lot_id, "PROCESSED")
    with pytest.raises(InvalidTransitionError):
        harness.run(
            "beneficiador",
            "record_processing",
            {"lot_id": lot_id, "description": "Segunda vez"},
        )


# ---------------------------------------------------------- access control
def test_stage_operations_require_the_matching_role(harness, wallets):
    lot_id = harness.register()
    with pytest.raises(AccessDeniedError):
        harness.run(
            "intruso",
            "record_processing",
            {"lot_id": lot_id, "description": "Fraude aqui"},
        )
    with pytest.raises(AccessDeniedError):
        harness.run(
            "produtor",
            "record_processing",
            {"lot_id": lot_id, "description": "Sem perfil"},
        )
    harness.advance_to(lot_id, "PROCESSED")
    with pytest.raises(AccessDeniedError):
        harness.run(
            "beneficiador",
            "start_transport",
            {
                "lot_id": lot_id,
                "recipient": wallets["distribuidor"].address,
                "destination": "Manaus",
            },
        )
    assert harness.contract.get_lot(lot_id).status is LotStatus.PROCESSED


def test_revoked_role_loses_access(harness, wallets):
    harness.run(
        "administrador",
        "revoke_role",
        {"account": wallets["produtor"].address, "role": "PRODUCER"},
    )
    with pytest.raises(AccessDeniedError):
        harness.run("produtor", "register_lot", VALID_LOT)


def test_transport_recipient_must_be_a_distributor(harness, wallets):
    lot_id = harness.register()
    harness.advance_to(lot_id, "PROCESSED")
    with pytest.raises(ContractValidationError):
        harness.run(
            "transportador",
            "start_transport",
            {
                "lot_id": lot_id,
                "recipient": wallets["intruso"].address,
                "destination": "Manaus",
            },
        )
    assert harness.contract.get_lot(lot_id).recipient is None


def test_only_the_designated_distributor_confirms_delivery(harness, wallets):
    other = wallets["intruso"]
    harness.run(
        "administrador", "grant_role", {"account": other.address, "role": "DISTRIBUTOR"}
    )
    lot_id = harness.register()
    harness.advance_to(lot_id, "IN_TRANSIT")
    with pytest.raises(AccessDeniedError):
        harness.run("intruso", "confirm_delivery", {"lot_id": lot_id})
    harness.run("distribuidor", "confirm_delivery", {"lot_id": lot_id})


def test_only_the_custodian_finalizes(harness, wallets):
    other = wallets["intruso"]
    harness.run(
        "administrador", "grant_role", {"account": other.address, "role": "DISTRIBUTOR"}
    )
    lot_id = harness.register()
    harness.advance_to(lot_id, "DISTRIBUTED")
    with pytest.raises(AccessDeniedError):
        harness.run("intruso", "finalize_lot", {"lot_id": lot_id})


# ------------------------------------------------------------- finalized lot
@pytest.mark.parametrize(
    "who, method, extra",
    [
        ("beneficiador", "record_processing", {"description": "Reprocessar"}),
        ("distribuidor", "finalize_lot", {}),
        ("distribuidor", "confirm_delivery", {}),
        (
            "distribuidor",
            "attach_document",
            {"document_hash": DOC_HASH, "description": "Novo laudo"},
        ),
    ],
)
def test_finalized_lot_is_immutable(harness, who, method, extra):
    lot_id = harness.register()
    harness.advance_to(lot_id, "FINALIZED")
    snapshot = harness.contract.get_lot(lot_id).to_dict()
    with pytest.raises(LotFinalizedError):
        harness.run(who, method, {"lot_id": lot_id, **extra})
    assert harness.contract.get_lot(lot_id).to_dict() == snapshot


# ----------------------------------------------------------------- lookups
@pytest.mark.parametrize("lot_id", ["LOT-0999", "LOT-9999"])
def test_operations_on_missing_lot_are_rejected(harness, lot_id):
    with pytest.raises(LotNotFoundError):
        harness.run(
            "beneficiador",
            "record_processing",
            {"lot_id": lot_id, "description": "Sem lote"},
        )
    with pytest.raises(LotNotFoundError):
        harness.contract.get_lot(lot_id)


@pytest.mark.parametrize("lot_id", ["", "lote-1", "LOT-1", 1, None])
def test_malformed_lot_id_is_rejected(harness, lot_id):
    with pytest.raises(ContractValidationError):
        harness.run(
            "beneficiador",
            "record_processing",
            {"lot_id": lot_id, "description": "Sem lote"},
        )


def test_list_lots_filters_by_status(harness):
    first, second = harness.register(), harness.register()
    harness.advance_to(second, "PROCESSED")
    assert [lot.lot_id for lot in harness.contract.list_lots()] == [first, second]
    assert [lot.lot_id for lot in harness.contract.list_lots("PROCESSED")] == [second]


def test_summary_counts_lots_by_status(harness):
    harness.register()
    lot_id = harness.register()
    harness.advance_to(lot_id, "PROCESSED")
    summary = harness.contract.summary()
    assert summary["lot_count"] == 2
    assert summary["lots_by_status"]["REGISTERED"] == 1
    assert summary["lots_by_status"]["PROCESSED"] == 1


# ---------------------------------------------------------------- documents
def test_custodian_attaches_and_verifies_documents(harness):
    lot_id = harness.register()
    harness.run(
        "produtor",
        "attach_document",
        {
            "lot_id": lot_id,
            "document_hash": DOC_HASH,
            "description": "Certificado orgânico",
        },
    )
    assert (
        harness.contract.verify_document(lot_id, DOC_HASH.upper())["description"]
        == "Certificado orgânico"
    )
    assert harness.contract.verify_document(lot_id, "b" * 64) is None


def test_document_rules(harness):
    lot_id = harness.register()
    args = {
        "lot_id": lot_id,
        "document_hash": DOC_HASH,
        "description": "Certificado orgânico",
    }
    harness.run("produtor", "attach_document", args)
    with pytest.raises(ContractValidationError):
        harness.run("produtor", "attach_document", args)
    with pytest.raises(AccessDeniedError):
        harness.run(
            "beneficiador", "attach_document", {**args, "document_hash": "c" * 64}
        )
    with pytest.raises(ContractValidationError):
        harness.run("produtor", "attach_document", {**args, "document_hash": "curto"})


def test_processing_can_attach_a_report_hash(harness):
    lot_id = harness.register()
    harness.run(
        "beneficiador",
        "record_processing",
        {"lot_id": lot_id, "description": "Beneficiamento", "document_hash": DOC_HASH},
    )
    assert (
        harness.contract.get_lot(lot_id).documents[0]["description"]
        == "Laudo de beneficiamento"
    )


def test_rejected_operations_never_change_state(harness, wallets):
    lot_id = harness.register()
    before = harness.contract.summary(), harness.contract.get_lot(lot_id).to_dict()
    attempts = [
        ("intruso", "register_lot", VALID_LOT),
        (
            "beneficiador",
            "start_transport",
            {
                "lot_id": lot_id,
                "recipient": wallets["distribuidor"].address,
                "destination": "Manaus",
            },
        ),
        ("distribuidor", "finalize_lot", {"lot_id": lot_id}),
        ("produtor", "register_lot", {**VALID_LOT, "quantity_kg": -1}),
    ]
    for who, method, args in attempts:
        with pytest.raises(Exception):
            harness.run(who, method, args)
    assert (
        harness.contract.summary(),
        harness.contract.get_lot(lot_id).to_dict(),
    ) == before
