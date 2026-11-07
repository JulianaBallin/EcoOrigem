"""Domain errors shared by the blockchain, the smart contract and the node.

Every error carries a stable ``code`` (consumed by the API, the interface and
the tests) and a human readable ``message`` written in Portuguese, since it is
shown to end users.
"""

from __future__ import annotations

from typing import Any


class EcoOrigemError(Exception):
    """Base class for all expected, user-facing errors."""

    code = "ERROR"
    layer = "node"
    http_status = 400

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize the error for API responses and the rejection log."""
        return {
            "code": self.code,
            "layer": self.layer,
            "message": self.message,
            "details": self.details,
        }


# --------------------------------------------------------------------------
# Transaction and node level errors (raised before the contract executes)
# --------------------------------------------------------------------------
class TransactionError(EcoOrigemError):
    """A transaction is not acceptable for the node."""

    layer = "transaction"


class MalformedTransactionError(TransactionError):
    """The transaction payload has missing fields or wrong types."""

    code = "MALFORMED_TRANSACTION"


class InvalidSignatureError(TransactionError):
    """The signature, the hash or the sender address do not match."""

    code = "INVALID_SIGNATURE"
    http_status = 401


class NonceError(TransactionError):
    """The transaction nonce is not the next one expected for the sender."""

    code = "NONCE_MISMATCH"
    http_status = 409


class StaleTimestampError(TransactionError):
    """The transaction timestamp is too far from the node clock."""

    code = "TIMESTAMP_OUT_OF_RANGE"


class DuplicateTransactionError(TransactionError):
    """The transaction was already accepted by the node."""

    code = "DUPLICATE_TRANSACTION"
    http_status = 409


class ContractNotDeployedError(TransactionError):
    """A contract call was sent before the contract was deployed."""

    code = "CONTRACT_NOT_DEPLOYED"
    http_status = 409


class ContractAlreadyDeployedError(TransactionError):
    """The chain already hosts a deployed EcoOrigem contract."""

    code = "CONTRACT_ALREADY_DEPLOYED"
    http_status = 409


class WrongContractError(TransactionError):
    """The transaction targets an address that is not the deployed contract."""

    code = "WRONG_CONTRACT"


class InvalidBlockError(EcoOrigemError):
    """A block cannot be appended to the chain."""

    code = "INVALID_BLOCK"


class ChainCompromisedError(TransactionError):
    """The local chain failed the integrity check; writes are blocked."""

    code = "CHAIN_COMPROMISED"
    layer = "node"
    http_status = 423


# --------------------------------------------------------------------------
# Smart contract errors (equivalent to a Solidity ``revert``)
# --------------------------------------------------------------------------
class ContractError(EcoOrigemError):
    """A business rule of the smart contract rejected the operation."""

    layer = "contract"
    http_status = 422


class UnknownMethodError(ContractError):
    """The requested contract method does not exist."""

    code = "UNKNOWN_METHOD"


class ContractValidationError(ContractError):
    """An argument is missing, has a wrong type or violates a limit."""

    code = "INVALID_INPUT"


class AccessDeniedError(ContractError):
    """The sender has no permission to execute the operation."""

    code = "ACCESS_DENIED"
    http_status = 403


class LotNotFoundError(ContractError):
    """The lot identifier does not exist in the contract."""

    code = "LOT_NOT_FOUND"
    http_status = 404


class InvalidTransitionError(ContractError):
    """The requested stage skips or repeats a mandatory step."""

    code = "INVALID_TRANSITION"


class LotFinalizedError(ContractError):
    """The lot is finalized and can no longer be changed."""

    code = "LOT_FINALIZED"
