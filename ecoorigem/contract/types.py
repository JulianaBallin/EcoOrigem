"""Data types used by the EcoOrigem smart contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Role(str, Enum):
    """Permission profiles granted by the contract administrator."""

    PRODUCER = "PRODUCER"
    PROCESSOR = "PROCESSOR"
    CARRIER = "CARRIER"
    DISTRIBUTOR = "DISTRIBUTOR"


class LotStatus(str, Enum):
    """Stages of the lot life cycle, in the mandatory order."""

    REGISTERED = "REGISTERED"
    PROCESSED = "PROCESSED"
    IN_TRANSIT = "IN_TRANSIT"
    DISTRIBUTED = "DISTRIBUTED"
    FINALIZED = "FINALIZED"


NEXT_STATUS: dict[LotStatus, LotStatus] = {
    LotStatus.REGISTERED: LotStatus.PROCESSED,
    LotStatus.PROCESSED: LotStatus.IN_TRANSIT,
    LotStatus.IN_TRANSIT: LotStatus.DISTRIBUTED,
    LotStatus.DISTRIBUTED: LotStatus.FINALIZED,
}

STATUS_LABELS: dict[str, str] = {
    LotStatus.REGISTERED.value: "CADASTRADO",
    LotStatus.PROCESSED.value: "BENEFICIADO",
    LotStatus.IN_TRANSIT.value: "EM_TRANSPORTE",
    LotStatus.DISTRIBUTED.value: "DISTRIBUIDO",
    LotStatus.FINALIZED.value: "FINALIZADO",
}

ROLE_LABELS: dict[str, str] = {
    Role.PRODUCER.value: "Produtor",
    Role.PROCESSOR.value: "Beneficiador",
    Role.CARRIER.value: "Transportador",
    Role.DISTRIBUTOR.value: "Distribuidor",
}

DEFAULT_PRODUCTS: tuple[str, ...] = (
    "Açaí",
    "Castanha-do-Brasil",
    "Murumuru",
    "Cupuaçu",
    "Andiroba",
    "Copaíba",
    "Guaraná",
    "Óleo vegetal",
    "Artesanato",
)


@dataclass(frozen=True)
class CallContext:
    """Execution context supplied by the node to every contract call."""

    sender: str
    timestamp: int
    tx_hash: str
    contract_address: str


@dataclass(frozen=True)
class ContractEvent:
    """A fact emitted by the contract, similar to a Solidity event."""

    name: str
    actor: str
    timestamp: int
    tx_hash: str
    lot_id: str | None = None
    from_status: str | None = None
    to_status: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event."""
        return {
            "name": self.name,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "tx_hash": self.tx_hash,
            "lot_id": self.lot_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "data": self.data,
        }


@dataclass
class Lot:  # pylint: disable=too-many-instance-attributes
    """A traceable lot of a bioeconomy product."""

    lot_id: str
    product: str
    origin: str
    quantity_kg: float
    harvest_date: str
    producer: str
    custodian: str
    status: LotStatus
    created_at: int
    updated_at: int
    recipient: str | None = None
    destination: str | None = None
    documents: list[dict[str, Any]] = field(default_factory=list)
    history: list[ContractEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the lot with both raw and display values of its status."""
        return {
            "lot_id": self.lot_id,
            "product": self.product,
            "origin": self.origin,
            "quantity_kg": self.quantity_kg,
            "harvest_date": self.harvest_date,
            "producer": self.producer,
            "custodian": self.custodian,
            "recipient": self.recipient,
            "destination": self.destination,
            "status": self.status.value,
            "status_label": STATUS_LABELS[self.status.value],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "documents": list(self.documents),
            "history": [event.to_dict() for event in self.history],
        }
