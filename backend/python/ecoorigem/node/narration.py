"""Plain language descriptions of node events for the terminal log.

Each function returns a title and a list of ``(field, value)`` details that the
log formatter prints as an indented block, so the audience of a demonstration
can follow what happened without reading method names or raw addresses.
"""

from __future__ import annotations

import time
from typing import Any

from ecoorigem.blockchain.block import Block
from ecoorigem.blockchain.chain import ValidationReport
from ecoorigem.blockchain.transaction import TX_DEPLOY, Transaction
from ecoorigem.contract import (
    ROLE_LABELS,
    STATUS_LABELS,
    ContractEvent,
    EcoOrigemContract,
)

Details = list[tuple[str, str]]

DONE: dict[str, str] = {
    "grant_role": "concedeu um perfil",
    "revoke_role": "revogou um perfil",
    "register_lot": "registrou um lote",
    "record_processing": "registrou o beneficiamento do lote",
    "start_transport": "iniciou o transporte do lote",
    "confirm_delivery": "confirmou o recebimento do lote",
    "finalize_lot": "finalizou o lote",
    "attach_document": "anexou um documento ao lote",
}
ATTEMPTED: dict[str, str] = {
    "grant_role": "conceder um perfil",
    "revoke_role": "revogar um perfil",
    "register_lot": "registrar um lote",
    "record_processing": "registrar o beneficiamento de um lote",
    "start_transport": "iniciar o transporte de um lote",
    "confirm_delivery": "confirmar o recebimento de um lote",
    "finalize_lot": "finalizar um lote",
    "attach_document": "anexar um documento a um lote",
}


def short(address: str | None) -> str:
    """Abbreviate an address, keeping the start and the end."""
    if not address:
        return "desconhecido"
    return f"{address[:6]}...{address[-4:]}"


def number(value: float, decimals: int = 0) -> str:
    """Format a number the Brazilian way (``36.291`` and ``0,19``)."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def actor(contract: EcoOrigemContract | None, address: str | None) -> str:
    """Name an account by its profile, followed by the short address."""
    if contract is not None and address == contract.admin:
        name = "Administrador"
    else:
        roles = contract.roles_of(address) if contract and address else []
        name = (
            ", ".join(ROLE_LABELS[role.value] for role in roles)
            or "Carteira sem perfil"
        )
    return f"{name} ({short(address)})"


def status_label(value: str | None) -> str:
    """Translate a lot status to the label shown in the interface."""
    return STATUS_LABELS.get(value or "", value or "")


def _action(tx: Transaction, events: list[ContractEvent]) -> str:
    if tx.tx_type == TX_DEPLOY:
        return "implantou o contrato EcoOrigem"
    lot = next((event.lot_id for event in events if event.lot_id), None)
    text = DONE.get(tx.method, f"executou {tx.method}")
    if tx.method == "register_lot":
        product = tx.args.get("product", "")
        quantity = tx.args.get("quantity_kg")
        extra = f"{product}, {number(float(quantity), 1)} kg" if quantity else product
        return f"registrou o lote {lot} ({extra})"
    if tx.method in {"grant_role", "revoke_role"}:
        role = ROLE_LABELS.get(str(tx.args.get("role")), str(tx.args.get("role")))
        verb = "concedeu" if tx.method == "grant_role" else "revogou"
        return f"{verb} o perfil {role} para {short(str(tx.args.get('account')))}"
    return f"{text} {lot}" if lot else text


def moment(timestamp_ms: int) -> str:
    """Format a millisecond timestamp as local date and time."""
    return time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(timestamp_ms / 1000))


def _value(value: Any) -> str:
    if isinstance(value, float):
        return number(value, 1)
    return str(value)


def block_data(block: Block) -> str:
    """Describe the data stored in a block: each transaction and its arguments."""
    if not block.transactions:
        return block.note or "sem transações"
    lines: list[str] = []
    for tx in block.transactions:
        lines.append(f"{tx.method} (transação {tx.hash[:16]}...)")
        lines.extend(f"  {key}: {_value(value)}" for key, value in tx.args.items())
    return "\n".join(lines)


def block_fields(block: Block) -> Details:
    """Return the classic fields of a block, as in the course example."""
    return [
        ("Índice", str(block.index)),
        ("Timestamp", f"{moment(block.timestamp)} ({block.timestamp})"),
        ("Dados", block_data(block)),
        ("Hash anterior", block.previous_hash),
        ("Hash", block.hash),
        ("Nonce", str(block.nonce)),
        ("Raiz de Merkle", block.merkle_root),
    ]


def link(block: Block, previous: Block | None) -> str:
    """Tell whether the block points to the hash of the previous block."""
    if previous is None:
        return "bloco gênesis, sem bloco anterior"
    if block.previous_hash == previous.hash:
        return f"hash anterior confere com o hash do bloco #{previous.index}"
    return f"QUEBRADO: hash anterior difere do hash do bloco #{previous.index}"


def _proof(block: Block, mining: dict[str, Any]) -> str:
    return (
        f"{number(mining['attempts'])} tentativas em {number(mining['seconds'], 2)} s,"
        f" hash começa com {block.difficulty} zeros"
    )


def confirmed(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    contract: EcoOrigemContract | None,
    tx: Transaction,
    events: list[ContractEvent],
    block: Block,
    previous: Block | None,
    mining: dict[str, Any],
) -> tuple[str, Details]:
    """Describe a transaction that was written into a new block."""
    details: Details = [
        ("Quem", actor(contract, tx.sender)),
        ("Ação", _action(tx, events)),
    ]
    change = next((event for event in events if event.to_status), None)
    if change is not None:
        before = status_label(change.from_status) or "novo"
        details.append(("Status", f"{before} para {status_label(change.to_status)}"))
    details.extend(block_fields(block))
    details.append(("Prova de trabalho", _proof(block, mining)))
    details.append(("Encadeamento", link(block, previous)))
    return f"BLOCO #{block.index} CONFIRMADO", details


def pending(contract: EcoOrigemContract | None, tx: Transaction) -> tuple[str, Details]:
    """Describe a transaction accepted while automatic mining is off."""
    return "TRANSAÇÃO PENDENTE", [
        ("Quem", actor(contract, tx.sender)),
        ("Ação", DONE.get(tx.method, tx.method)),
        ("Resultado", "aguardando a mineração manual"),
    ]


def mined(
    block: Block, previous: Block | None, mining: dict[str, Any]
) -> tuple[str, Details]:
    """Describe a block mined on demand with the pending transactions."""
    details: Details = [("Transações", number(len(block.transactions)))]
    details.extend(block_fields(block))
    details.append(("Prova de trabalho", _proof(block, mining)))
    details.append(("Encadeamento", link(block, previous)))
    return f"BLOCO #{block.index} MINERADO", details


def rejected(
    contract: EcoOrigemContract | None,
    sender: str | None,
    method: str | None,
    code: str,
    message: str,
) -> tuple[str, Details]:
    """Describe an operation refused by the node or the contract."""
    return "OPERAÇÃO REJEITADA", [
        ("Quem", actor(contract, sender)),
        ("Tentou", ATTEMPTED.get(method or "", method or "operação desconhecida")),
        ("Motivo", message),
        ("Código", code),
        ("Resultado", "nenhum bloco criado, contrato inalterado"),
    ]


def tampered(block_index: int, report: ValidationReport) -> tuple[str, Details]:
    """Describe the tampering simulation of the integrity laboratory."""
    if report.valid:
        return "ALTERAÇÃO NÃO DETECTADA", [("Bloco alterado", f"#{block_index}")]
    return "ADULTERAÇÃO DETECTADA", [
        ("Bloco alterado", f"#{block_index}"),
        ("Primeiro inválido", f"#{report.first_invalid_block}"),
        ("Resultado", "novas operações bloqueadas até restaurar"),
    ]


def restored(report: ValidationReport) -> tuple[str, Details]:
    """Describe the chain reloaded from disk."""
    state = "válida" if report.valid else "com falhas"
    return "CADEIA RESTAURADA", [
        ("Blocos verificados", number(report.checked_blocks)),
        ("Integridade", state),
    ]


def started(status: dict[str, Any], mode: str) -> tuple[str, Details]:
    """Describe the node right after it starts."""
    integrity = (
        "válida" if status["integrity"]["valid"] else "FALHOU, escritas bloqueadas"
    )
    return "BLOCKCHAIN INICIADA", [
        ("Blocos", number(status["height"])),
        ("Dificuldade", f"{status['difficulty']} zeros no início do hash"),
        ("Mineração", mode),
        ("Integridade", integrity),
    ]
