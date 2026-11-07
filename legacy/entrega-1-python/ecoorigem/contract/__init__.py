"""EcoOrigem smart contract package."""

from ecoorigem.contract.eco_origem import (
    CONTRACT_NAME,
    EcoOrigemContract,
    contract_address,
)
from ecoorigem.contract.types import (
    ROLE_LABELS,
    STATUS_LABELS,
    CallContext,
    ContractEvent,
    Lot,
    LotStatus,
    Role,
)

__all__ = [
    "CONTRACT_NAME",
    "ROLE_LABELS",
    "STATUS_LABELS",
    "CallContext",
    "ContractEvent",
    "EcoOrigemContract",
    "Lot",
    "LotStatus",
    "Role",
    "contract_address",
]
