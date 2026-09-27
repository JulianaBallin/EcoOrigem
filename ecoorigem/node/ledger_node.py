"""The local blockchain node.

The node owns the chain and the state of the smart contract. It accepts signed
transactions, checks them (signature, replay protection, clock, contract
rules), mines them into blocks with proof of work and persists the result. It
never holds private keys: signing is the job of the wallets.
"""

from __future__ import annotations

import threading
import time
from dataclasses import replace
from typing import Any, Callable

from ecoorigem.blockchain.block import Block
from ecoorigem.blockchain.chain import Blockchain, ValidationReport
from ecoorigem.blockchain.merkle import merkle_proof, verify_merkle_proof
from ecoorigem.blockchain.transaction import TX_DEPLOY, Transaction, now_ms
from ecoorigem.contract import (
    CONTRACT_NAME,
    ROLE_LABELS,
    STATUS_LABELS,
    CallContext,
    ContractEvent,
    EcoOrigemContract,
    Role,
    contract_address,
)
from ecoorigem.contract.types import LotStatus
from ecoorigem.errors import (
    ChainCompromisedError,
    ContractAlreadyDeployedError,
    ContractNotDeployedError,
    DuplicateTransactionError,
    EcoOrigemError,
    NonceError,
    StaleTimestampError,
    TransactionError,
    WrongContractError,
)
from ecoorigem.logs import get_logger
from ecoorigem.node.storage import LedgerStore

LOG = get_logger("node")

DEFAULT_MAX_CLOCK_SKEW_MS = 5 * 60 * 1000
MAX_PAGE_SIZE = 200


class LedgerNode:  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """A single-process blockchain node with an embedded smart contract."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        store: LedgerStore,
        difficulty: int = 4,
        auto_mine: bool = True,
        lab_enabled: bool = True,
        clock: Callable[[], int] = now_ms,
        max_clock_skew_ms: int = DEFAULT_MAX_CLOCK_SKEW_MS,
    ) -> None:
        self.store = store
        self.difficulty = difficulty
        self.auto_mine = auto_mine
        self.lab_enabled = lab_enabled
        self.clock = clock
        self.max_clock_skew_ms = max_clock_skew_ms
        self.started_at = clock()
        self._lock = threading.RLock()
        self.chain: Blockchain
        self.contract: EcoOrigemContract | None = None
        self.mempool: list[Transaction] = []
        self.last_mining: dict[str, Any] | None = None
        self._nonces: dict[str, int] = {}
        self._tx_location: dict[str, tuple[int, int]] = {}
        self._integrity = ValidationReport()
        self._rejections: list[dict[str, Any]] = []
        self._load()

    # ------------------------------------------------------------------
    # Start-up, replay and integrity
    # ------------------------------------------------------------------
    def _load(self) -> None:
        """Load the chain from disk (or create it) and rebuild the state."""
        with self._lock:
            raw = self.store.load_chain()
            if raw is None:
                self.chain = Blockchain.create(self.difficulty, self.clock())
                self.store.save_chain(self.chain.to_dict())
            else:
                try:
                    self.chain = Blockchain.from_dict(raw)
                except (KeyError, TypeError, ValueError, EcoOrigemError) as error:
                    raise TransactionError(
                        "O arquivo da blockchain está corrompido e não pode ser "
                        f"interpretado: {error}"
                    ) from error
                self.difficulty = self.chain.difficulty
            self.mempool = []
            self._rejections = self.store.load_rejections()
            self._rebuild()

    def _rebuild(self) -> None:
        """Replay the chain to rebuild the contract state and refresh integrity."""
        contract, nonces, location, replay_issues = self._replay(self.chain)
        report = self.chain.validate()
        for block_index, message in replay_issues:
            report.add(block_index, "CONTRACT_REPLAY_FAILED", message)
        self.contract = contract
        self._nonces = nonces
        self._tx_location = location
        self._integrity = report

    def _replay(self, chain: Blockchain) -> tuple[
        EcoOrigemContract | None,
        dict[str, int],
        dict[str, tuple[int, int]],
        list[tuple[int, str]],
    ]:
        """Execute every stored transaction on a fresh contract."""
        contract: EcoOrigemContract | None = None
        nonces: dict[str, int] = {}
        location: dict[str, tuple[int, int]] = {}
        issues: list[tuple[int, str]] = []
        for block in chain.blocks:
            for position, tx in enumerate(block.transactions):
                location[tx.hash] = (block.index, position)
                nonces[tx.sender] = tx.nonce + 1
                try:
                    contract, _ = self._execute(contract, tx)
                except EcoOrigemError as error:
                    issues.append((block.index, error.message))
        return contract, nonces, location, issues

    @staticmethod
    def _execute(
        contract: EcoOrigemContract | None, tx: Transaction
    ) -> tuple[EcoOrigemContract, list[ContractEvent]]:
        """Run one transaction against ``contract`` and return the new contract."""
        if tx.tx_type == TX_DEPLOY:
            if contract is not None:
                raise ContractAlreadyDeployedError(
                    "O contrato EcoOrigem já foi implantado nesta blockchain."
                )
            ctx = CallContext(
                sender=tx.sender,
                timestamp=tx.timestamp,
                tx_hash=tx.hash,
                contract_address=contract_address(tx.sender, tx.nonce),
            )
            deployed = EcoOrigemContract.deploy(ctx, tx.args)
            return deployed, list(deployed.events)
        if contract is None:
            raise ContractNotDeployedError(
                "O contrato ainda não foi implantado. Execute a implantação primeiro."
            )
        if tx.to != contract.address:
            raise WrongContractError(
                "O destino não corresponde ao contrato implantado."
            )
        ctx = CallContext(tx.sender, tx.timestamp, tx.hash, contract.address)
        return contract, contract.execute(ctx, tx.method, tx.args)

    def validate(self) -> ValidationReport:
        """Run the full integrity check and update the write lock.

        The live contract state is kept; only the integrity report changes.
        """
        with self._lock:
            report = self.chain.validate()
            _, _, _, issues = self._replay(self.chain)
            for block_index, message in issues:
                report.add(block_index, "CONTRACT_REPLAY_FAILED", message)
            self._integrity = report
            return report

    @property
    def integrity_ok(self) -> bool:
        """Whether the last integrity check passed."""
        return self._integrity.valid

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------
    def submit_transaction(self, raw: Any) -> dict[str, Any]:
        """Validate, execute and (with auto mining) mine a signed transaction.

        Returns a receipt. Raises an :class:`EcoOrigemError` when the operation
        is rejected; every rejection is also recorded in the rejection log.
        """
        with self._lock:
            try:
                return self._submit(raw)
            except EcoOrigemError as error:
                self._record_rejection(raw, error)
                raise

    def _submit(self, raw: Any) -> dict[str, Any]:
        if not self.integrity_ok:
            raise ChainCompromisedError(
                "A integridade da blockchain falhou. Novas operações estão bloqueadas "
                "até a cadeia ser restaurada."
            )
        tx = Transaction.from_dict(raw)
        tx.verify()
        self._check_intake(tx)
        contract, events = self._execute(self.contract, tx)
        self.contract = contract
        self._nonces[tx.sender] = tx.nonce + 1
        self.mempool.append(tx)
        block: Block | None = None
        if self.auto_mine:
            block = self._mine()
        return self._receipt(tx, events, block)

    def _check_intake(self, tx: Transaction) -> None:
        if tx.hash in self._tx_location or any(p.hash == tx.hash for p in self.mempool):
            raise DuplicateTransactionError("Esta transação já foi registrada.")
        drift = abs(self.clock() - tx.timestamp)
        if drift > self.max_clock_skew_ms:
            raise StaleTimestampError(
                "A data da transação difere demais do relógio do nó.",
                {"drift_ms": drift, "limit_ms": self.max_clock_skew_ms},
            )
        expected = self._nonces.get(tx.sender, 0)
        if tx.nonce != expected:
            raise NonceError(
                f"Nonce inválido: esperado {expected}, recebido {tx.nonce}. "
                "A transação pode ser uma repetição.",
                {"expected": expected, "received": tx.nonce},
            )

    def mine_pending(self) -> Block | None:
        """Mine all pending transactions into one block."""
        with self._lock:
            if not self.mempool:
                return None
            return self._mine()

    def _mine(self) -> Block:
        started = time.perf_counter()
        pending = list(self.mempool)
        try:
            block, attempts = self.chain.mine_block(pending, self.clock())
            self.chain.append(block)
            try:
                self.store.save_chain(self.chain.to_dict())
            except BaseException:
                self.chain.blocks.pop()
                raise
        except BaseException:
            self.mempool = []
            self._rebuild()
            raise
        for position, tx in enumerate(block.transactions):
            self._tx_location[tx.hash] = (block.index, position)
        self.mempool = []
        self.last_mining = {
            "block_index": block.index,
            "attempts": attempts,
            "seconds": round(time.perf_counter() - started, 4),
            "difficulty": block.difficulty,
        }
        LOG.info(
            "Bloco #%d minerado com %s: %d tentativas de nonce em %.2f s, hash %s...",
            block.index,
            ", ".join(_describe(tx) for tx in block.transactions),
            attempts,
            self.last_mining["seconds"],
            block.hash[:16],
            extra={"tone": "ok", "label": "BLOCO"},
        )
        return block

    def _receipt(
        self, tx: Transaction, events: list[ContractEvent], block: Block | None
    ) -> dict[str, Any]:
        return {
            "status": "confirmed" if block else "pending",
            "tx_hash": tx.hash,
            "block_index": block.index if block else None,
            "block_hash": block.hash if block else None,
            "contract_address": self.contract.address if self.contract else None,
            "events": [event.to_dict() for event in events],
            "mining": self.last_mining if block else None,
        }

    def _record_rejection(self, raw: Any, error: EcoOrigemError) -> None:
        data = raw if isinstance(raw, dict) else {}
        entry = {
            "timestamp": self.clock(),
            "sender": (
                data.get("sender") if isinstance(data.get("sender"), str) else None
            ),
            "method": (
                data.get("method") if isinstance(data.get("method"), str) else None
            ),
            "code": error.code,
            "layer": error.layer,
            "message": error.message,
        }
        self._rejections.append(entry)
        self._rejections = self._rejections[-500:]
        self.store.append_rejection(entry)
        LOG.warning(
            "%s em %s por %s: %s Nenhum bloco criado.",
            error.code,
            entry["method"] or "operação",
            _short(entry["sender"]),
            error.message,
            extra={"tone": "bad", "label": "REJEITADA"},
        )

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------
    def status(self) -> dict[str, Any]:
        """Return an overview of the node for dashboards and health checks."""
        with self._lock:
            return {
                "height": len(self.chain),
                "difficulty": self.chain.difficulty,
                "tip_hash": self.chain.tip.hash,
                "genesis_hash": self.chain.blocks[0].hash,
                "transactions": len(self._tx_location),
                "pending": len(self.mempool),
                "auto_mine": self.auto_mine,
                "lab_enabled": self.lab_enabled,
                "started_at": self.started_at,
                "last_mining": self.last_mining,
                "rejections": len(self._rejections),
                "integrity": {
                    "valid": self._integrity.valid,
                    "first_invalid_block": self._integrity.first_invalid_block,
                    "issue_count": len(self._integrity.issues),
                },
                "contract": {
                    "deployed": self.contract is not None,
                    "name": CONTRACT_NAME,
                    "address": self.contract.address if self.contract else None,
                    "admin": self.contract.admin if self.contract else None,
                },
            }

    def blocks(
        self, offset: int = 0, limit: int = 20, newest_first: bool = True
    ) -> dict[str, Any]:
        """Return a page of blocks."""
        with self._lock:
            limit = max(1, min(limit, MAX_PAGE_SIZE))
            offset = max(0, offset)
            ordered = (
                list(reversed(self.chain.blocks)) if newest_first else self.chain.blocks
            )
            page = ordered[offset : offset + limit]
            return {
                "total": len(self.chain),
                "offset": offset,
                "limit": limit,
                "blocks": [self._block_view(block) for block in page],
            }

    def block(self, index: int) -> dict[str, Any] | None:
        """Return one block or ``None``."""
        with self._lock:
            if 0 <= index < len(self.chain):
                return self._block_view(self.chain.blocks[index])
            return None

    @staticmethod
    def _block_view(block: Block) -> dict[str, Any]:
        view = block.to_dict()
        view["transaction_count"] = len(block.transactions)
        return view

    def transaction(self, tx_hash: str) -> dict[str, Any] | None:
        """Return a transaction with its block position and contract events."""
        with self._lock:
            location = self._tx_location.get(tx_hash)
            if location is None:
                pending = next((tx for tx in self.mempool if tx.hash == tx_hash), None)
                if pending is None:
                    return None
                return {**pending.to_dict(), "status": "pending", "block_index": None}
            block = self.chain.blocks[location[0]]
            tx = block.transactions[location[1]]
            events = [
                event.to_dict()
                for event in (self.contract.events if self.contract else [])
                if event.tx_hash == tx_hash
            ]
            return {
                **tx.to_dict(),
                "status": "confirmed",
                "block_index": block.index,
                "block_hash": block.hash,
                "events": events,
            }

    def inclusion_proof(self, tx_hash: str) -> dict[str, Any] | None:
        """Return the Merkle inclusion proof of a confirmed transaction."""
        with self._lock:
            location = self._tx_location.get(tx_hash)
            if location is None:
                return None
            block = self.chain.blocks[location[0]]
            leaves = [tx.hash for tx in block.transactions]
            proof = merkle_proof(leaves, location[1])
            return {
                "tx_hash": tx_hash,
                "block_index": block.index,
                "merkle_root": block.merkle_root,
                "proof": proof,
                "valid": verify_merkle_proof(tx_hash, proof, block.merkle_root),
            }

    def account(self, address: str) -> dict[str, Any]:
        """Return the nonce and the roles of an account."""
        with self._lock:
            roles = self.contract.roles_of(address) if self.contract else []
            return {
                "address": address,
                "nonce": self._nonces.get(address, 0),
                "is_admin": bool(self.contract and self.contract.admin == address),
                "roles": [role.value for role in roles],
                "role_labels": [ROLE_LABELS[role.value] for role in roles],
            }

    def contract_summary(self) -> dict[str, Any] | None:
        """Return the deployed contract description, or ``None``."""
        with self._lock:
            if self.contract is None:
                return None
            summary = self.contract.summary()
            summary["deployed_block"] = self._block_of(self.contract.deploy_tx_hash)
            summary["status_labels"] = STATUS_LABELS
            summary["role_labels"] = ROLE_LABELS
            summary["status_order"] = [status.value for status in LotStatus]
            summary["all_roles"] = [role.value for role in Role]
            return summary

    def _block_of(self, tx_hash: str) -> int | None:
        location = self._tx_location.get(tx_hash)
        return location[0] if location else None

    def lots(self, status: str | None = None) -> list[dict[str, Any]]:
        """Return the lots recorded in the contract."""
        with self._lock:
            if self.contract is None:
                return []
            return [
                self._lot_view(lot.to_dict()) for lot in self.contract.list_lots(status)
            ]

    def lot(self, lot_id: str) -> dict[str, Any]:
        """Return one lot; raises ``LotNotFoundError`` when it does not exist."""
        with self._lock:
            if self.contract is None:
                raise ContractNotDeployedError("O contrato ainda não foi implantado.")
            return self._lot_view(self.contract.get_lot(lot_id).to_dict())

    def _lot_view(self, lot: dict[str, Any]) -> dict[str, Any]:
        """Attach block references to the history and documents of a lot."""
        for event in lot["history"]:
            event["block_index"] = self._block_of(event["tx_hash"])
            event["from_status_label"] = STATUS_LABELS.get(event["from_status"] or "")
            event["to_status_label"] = STATUS_LABELS.get(event["to_status"] or "")
        for document in lot["documents"]:
            document["block_index"] = self._block_of(document["tx_hash"])
        return lot

    def verify_document(self, lot_id: str, digest: str) -> dict[str, Any]:
        """Check whether a document hash is registered for a lot."""
        with self._lock:
            if self.contract is None:
                raise ContractNotDeployedError("O contrato ainda não foi implantado.")
            document = self.contract.verify_document(lot_id, digest)
            return {
                "lot_id": lot_id,
                "hash": digest.lower(),
                "registered": document is not None,
                "document": document,
            }

    def rejections(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return the latest rejected operations, newest first."""
        with self._lock:
            return list(reversed(self._rejections[-max(1, limit) :]))

    # ------------------------------------------------------------------
    # Integrity laboratory (academic demonstration only)
    # ------------------------------------------------------------------
    def lab_tamper(
        self, block_index: int, changes: dict[str, Any], remine: bool = False
    ) -> ValidationReport:
        """Alter a stored transaction in memory to show how tampering is detected.

        The file on disk is not modified. With ``remine`` the attacker also
        recomputes the Merkle root and re-mines the block, which is detected
        by the broken link with the following block.
        """
        with self._lock:
            if not self.lab_enabled:
                raise TransactionError("O laboratório de integridade está desativado.")
            if not 1 <= block_index < len(self.chain):
                raise TransactionError(
                    "Escolha um bloco existente diferente do gênesis."
                )
            block = self.chain.blocks[block_index]
            if not block.transactions or not changes:
                raise TransactionError(
                    "O bloco não possui transações ou não há alterações."
                )
            original = block.transactions[0]
            block.transactions[0] = replace(original, args={**original.args, **changes})
            if remine:
                block.merkle_root = block.compute_merkle_root()
                block.mine()
            report = self.validate()
            LOG.warning(
                "Bloco #%d adulterado em memória. Integridade: %s. "
                "Escritas bloqueadas.",
                block_index,
                "válida" if report.valid else "FALHOU",
                extra={"tone": "warn", "label": "INTEGRIDADE"},
            )
            return report

    def lab_restore(self) -> ValidationReport:
        """Reload the chain from disk, discarding in-memory tampering."""
        with self._lock:
            self._load()
            LOG.info(
                "Cadeia restaurada da cópia em disco. Integridade: %s.",
                "válida" if self._integrity.valid else "FALHOU",
                extra={"tone": "ok", "label": "INTEGRIDADE"},
            )
            return self._integrity


def _short(address: str | None) -> str:
    """Abbreviate an address for log lines."""
    if not address:
        return "remetente desconhecido"
    return f"{address[:6]}...{address[-4:]}"


def _describe(tx: Transaction) -> str:
    """Summarize a transaction as ``method (sender)`` for log lines."""
    return f"{tx.method} ({_short(tx.sender)})"
