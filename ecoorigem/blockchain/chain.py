"""The blockchain: an ordered, hash-linked list of blocks with validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ecoorigem.blockchain.block import GENESIS_PREVIOUS_HASH, Block
from ecoorigem.blockchain.transaction import Transaction
from ecoorigem.errors import EcoOrigemError, InvalidBlockError

GENESIS_NOTE = "Bloco gênesis do EcoOrigem"


@dataclass(frozen=True)
class ValidationIssue:
    """A single integrity problem found while validating the chain."""

    block_index: int | None
    code: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the issue."""
        return {
            "block_index": self.block_index,
            "code": self.code,
            "message": self.message,
        }


@dataclass
class ValidationReport:
    """Result of validating a chain."""

    checked_blocks: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        """``True`` when no integrity problem was found."""
        return not self.issues

    @property
    def first_invalid_block(self) -> int | None:
        """Index of the first block that has a problem, if any."""
        indexes = [i.block_index for i in self.issues if i.block_index is not None]
        return min(indexes) if indexes else None

    def add(self, block_index: int | None, code: str, message: str) -> None:
        """Register an issue."""
        self.issues.append(ValidationIssue(block_index, code, message))

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report."""
        return {
            "valid": self.valid,
            "checked_blocks": self.checked_blocks,
            "first_invalid_block": self.first_invalid_block,
            "issues": [issue.to_dict() for issue in self.issues],
        }


class Blockchain:
    """Ordered list of blocks secured by SHA-256 links and proof of work."""

    def __init__(self, blocks: list[Block]) -> None:
        if not blocks:
            raise ValueError("A blockchain needs at least the genesis block.")
        self.blocks = blocks

    @classmethod
    def create(cls, difficulty: int, timestamp: int, note: str = GENESIS_NOTE):
        """Create a new chain containing only a mined genesis block."""
        return cls([Block.genesis(difficulty, timestamp, note)])

    @property
    def difficulty(self) -> int:
        """Difficulty defined by the genesis block."""
        return self.blocks[0].difficulty

    @property
    def tip(self) -> Block:
        """The most recent block."""
        return self.blocks[-1]

    def __len__(self) -> int:
        return len(self.blocks)

    # ------------------------------------------------------------------
    # Mining and appending
    # ------------------------------------------------------------------
    def mine_block(
        self, transactions: list[Transaction], timestamp: int, note: str = ""
    ) -> tuple[Block, int]:
        """Build and mine the next block. Returns the block and the attempts."""
        block = Block(
            index=self.tip.index + 1,
            timestamp=max(timestamp, self.tip.timestamp),
            previous_hash=self.tip.hash,
            transactions=list(transactions),
            difficulty=self.difficulty,
            note=note,
        )
        attempts = block.mine()
        return block, attempts

    def append(self, block: Block) -> None:
        """Append ``block`` after checking its link, hash and proof of work."""
        if block.index != self.tip.index + 1:
            raise InvalidBlockError("Índice de bloco inesperado.")
        if block.previous_hash != self.tip.hash:
            raise InvalidBlockError("O bloco não referencia o hash do bloco anterior.")
        if block.hash != block.compute_hash():
            raise InvalidBlockError("O hash do bloco não corresponde ao seu conteúdo.")
        if block.difficulty != self.difficulty or not block.meets_difficulty():
            raise InvalidBlockError("Prova de trabalho inválida.")
        if block.merkle_root != block.compute_merkle_root():
            raise InvalidBlockError("A raiz de Merkle não corresponde às transações.")
        self.blocks.append(block)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate(self) -> ValidationReport:
        """Check the integrity of the whole chain.

        Every block is verified against its predecessor, its own hash, the
        proof of work, the Merkle root and the signature of each transaction.
        The result lists every problem found instead of stopping at the first.
        """
        report = ValidationReport(checked_blocks=len(self.blocks))
        self._validate_genesis(report)
        next_nonce: dict[str, int] = {}
        seen: set[str] = set()
        for position, block in enumerate(self.blocks):
            if position > 0:
                self._validate_link(block, self.blocks[position - 1], report)
            self._validate_block_body(block, report)
            self._validate_transactions(block, next_nonce, seen, report)
        return report

    def _validate_genesis(self, report: ValidationReport) -> None:
        genesis = self.blocks[0]
        if (
            genesis.index != 0
            or genesis.previous_hash != GENESIS_PREVIOUS_HASH
            or genesis.transactions
        ):
            report.add(0, "GENESIS_INVALID", "O bloco gênesis está fora do padrão.")

    @staticmethod
    def _validate_link(block: Block, previous: Block, report: ValidationReport) -> None:
        if block.index != previous.index + 1:
            report.add(block.index, "BAD_INDEX", "Sequência de índices interrompida.")
        if block.previous_hash != previous.hash:
            report.add(
                block.index,
                "BROKEN_LINK",
                f"O hash anterior não coincide com o hash do bloco {previous.index}.",
            )
        if block.timestamp < previous.timestamp:
            report.add(
                block.index, "TIMESTAMP_ORDER", "Data anterior à do bloco precedente."
            )

    def _validate_block_body(self, block: Block, report: ValidationReport) -> None:
        if block.hash != block.compute_hash():
            report.add(
                block.index,
                "HASH_MISMATCH",
                "O hash armazenado não corresponde ao conteúdo do cabeçalho.",
            )
        if block.difficulty != self.difficulty or not block.meets_difficulty():
            report.add(
                block.index,
                "POW_INVALID",
                "O hash não atende à dificuldade da prova de trabalho.",
            )
        if block.merkle_root != block.compute_merkle_root():
            report.add(
                block.index,
                "MERKLE_MISMATCH",
                "As transações não correspondem à raiz de Merkle do bloco.",
            )

    @staticmethod
    def _validate_transactions(
        block: Block,
        next_nonce: dict[str, int],
        seen: set[str],
        report: ValidationReport,
    ) -> None:
        for tx in block.transactions:
            try:
                tx.verify()
            except EcoOrigemError as error:
                report.add(block.index, "TX_SIGNATURE_INVALID", error.message)
            if tx.hash in seen:
                report.add(block.index, "DUPLICATE_TX", "Transação repetida na cadeia.")
            seen.add(tx.hash)
            expected = next_nonce.get(tx.sender, 0)
            if tx.nonce != expected:
                report.add(
                    block.index,
                    "TX_NONCE_INVALID",
                    f"Nonce {tx.nonce} inesperado para {tx.sender} "
                    f"(esperado {expected}).",
                )
            next_nonce[tx.sender] = tx.nonce + 1

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """Serialize the chain."""
        return {"blocks": [block.to_dict() for block in self.blocks]}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Blockchain":
        """Rebuild a chain from stored data, preserving the stored hashes."""
        return cls([Block.from_dict(block) for block in raw["blocks"]])
