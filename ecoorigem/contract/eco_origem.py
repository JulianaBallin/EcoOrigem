"""EcoOrigem smart contract.

The contract holds the traceability rules of the supply chain. It is executed
by every node when a transaction is included in a block, and its state is a
pure function of the transactions stored in the chain: replaying the chain
from the genesis block always rebuilds the same state.

Every public operation follows the checks-effects pattern used in Solidity:
permissions and inputs are verified first, and the state is only changed after
every check has passed. A failed check raises a
:class:`~ecoorigem.errors.ContractError`, the equivalent of a ``revert``.
"""

from __future__ import annotations

import hashlib
from typing import Any, Callable

from ecoorigem.contract.types import (
    DEFAULT_PRODUCTS,
    NEXT_STATUS,
    ROLE_LABELS,
    STATUS_LABELS,
    CallContext,
    ContractEvent,
    Lot,
    LotStatus,
    Role,
)
from ecoorigem.contract.validation import (
    address_field,
    date_of,
    fold,
    harvest_date_field,
    lot_id_field,
    parse_args,
    quantity_field,
    role_field,
    sha256_field,
    text_field,
)
from ecoorigem.errors import (
    AccessDeniedError,
    ContractValidationError,
    InvalidTransitionError,
    LotFinalizedError,
    LotNotFoundError,
    UnknownMethodError,
)

CONTRACT_NAME = "EcoOrigem"
MAX_PRODUCTS = 30

note_text = text_field(3, 500)
place_text = text_field(3, 120)
product_text = text_field(2, 40)


def contract_address(deployer: str, nonce: int) -> str:
    """Derive the contract address from the deployer account and its nonce."""
    digest = hashlib.sha256(f"contract:{deployer}:{nonce}".encode()).hexdigest()
    return "0x" + digest[:40]


class EcoOrigemContract:  # pylint: disable=too-many-public-methods
    """State and rules of the traceability contract."""

    def __init__(
        self,
        address: str,
        admin: str,
        allowed_products: tuple[str, ...],
        deployed_at: int,
        deploy_tx_hash: str,
    ) -> None:
        self.address = address
        self.admin = admin
        self.allowed_products = allowed_products
        self.deployed_at = deployed_at
        self.deploy_tx_hash = deploy_tx_hash
        self.roles: dict[str, set[Role]] = {}
        self.lots: dict[str, Lot] = {}
        self.events: list[ContractEvent] = []
        self._lot_counter = 0
        self._methods: dict[str, Callable[[CallContext, dict[str, Any]], None]] = {
            "grant_role": self._grant_role,
            "revoke_role": self._revoke_role,
            "register_lot": self._register_lot,
            "record_processing": self._record_processing,
            "start_transport": self._start_transport,
            "confirm_delivery": self._confirm_delivery,
            "finalize_lot": self._finalize_lot,
            "attach_document": self._attach_document,
        }

    # ------------------------------------------------------------------
    # Deployment
    # ------------------------------------------------------------------
    @classmethod
    def deploy(cls, ctx: CallContext, args: dict[str, Any]) -> "EcoOrigemContract":
        """Create the contract. The sender becomes the administrator.

        ``ctx.contract_address`` must already hold the address derived by the
        node from the deployer and its nonce.
        """
        parsed = parse_args(
            args,
            required={},
            optional={"allowed_products": _products_field},
        )
        products = parsed.get("allowed_products", DEFAULT_PRODUCTS)
        contract = cls(
            address=ctx.contract_address,
            admin=ctx.sender,
            allowed_products=tuple(products),
            deployed_at=ctx.timestamp,
            deploy_tx_hash=ctx.tx_hash,
        )
        contract._emit(ctx, "CONTRACT_DEPLOYED", data={"admin": ctx.sender})
        return contract

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------
    @property
    def method_names(self) -> tuple[str, ...]:
        """Names of the state-changing methods."""
        return tuple(self._methods)

    def execute(
        self, ctx: CallContext, method: str, args: dict[str, Any]
    ) -> list[ContractEvent]:
        """Execute a state-changing method and return the events it emitted."""
        handler = self._methods.get(method)
        if handler is None:
            raise UnknownMethodError(f"Método inexistente no contrato: {method}.")
        before = len(self.events)
        handler(ctx, args)
        return self.events[before:]

    # ------------------------------------------------------------------
    # Administration
    # ------------------------------------------------------------------
    def _grant_role(self, ctx: CallContext, args: dict[str, Any]) -> None:
        self._require_admin(ctx)
        parsed = parse_args(args, {"account": address_field, "role": role_field})
        account, role = parsed["account"], parsed["role"]
        if role in self.roles.get(account, set()):
            raise ContractValidationError(
                f"A conta já possui o perfil {ROLE_LABELS[role.value]}."
            )
        self.roles.setdefault(account, set()).add(role)
        self._emit(ctx, "ROLE_GRANTED", data={"account": account, "role": role.value})

    def _revoke_role(self, ctx: CallContext, args: dict[str, Any]) -> None:
        self._require_admin(ctx)
        parsed = parse_args(args, {"account": address_field, "role": role_field})
        account, role = parsed["account"], parsed["role"]
        if role not in self.roles.get(account, set()):
            raise ContractValidationError(
                f"A conta não possui o perfil {ROLE_LABELS[role.value]}."
            )
        self.roles[account].discard(role)
        if not self.roles[account]:
            del self.roles[account]
        self._emit(ctx, "ROLE_REVOKED", data={"account": account, "role": role.value})

    # ------------------------------------------------------------------
    # Lot life cycle
    # ------------------------------------------------------------------
    def _register_lot(self, ctx: CallContext, args: dict[str, Any]) -> None:
        self._require_role(ctx, Role.PRODUCER)
        today = date_of(ctx.timestamp)
        parsed = parse_args(
            args,
            required={
                "product": self._product_field,
                "origin": place_text,
                "quantity_kg": quantity_field,
                "harvest_date": lambda name, value: harvest_date_field(
                    name, value, today
                ),
            },
            optional={
                "processor": address_field,
                "document_hash": sha256_field,
            },
        )
        processor = self._resolve_designated_actor(
            parsed.get("processor"), Role.PROCESSOR
        )

        self._lot_counter += 1
        lot_id = f"LOT-{self._lot_counter:04d}"
        lot = Lot(
            lot_id=lot_id,
            product=parsed["product"],
            origin=parsed["origin"],
            quantity_kg=parsed["quantity_kg"],
            harvest_date=parsed["harvest_date"],
            producer=ctx.sender,
            custodian=ctx.sender,
            status=LotStatus.REGISTERED,
            created_at=ctx.timestamp,
            updated_at=ctx.timestamp,
            processor=processor,
        )
        self.lots[lot_id] = lot
        self._attach(lot, ctx, parsed.get("document_hash"), "Documento de origem")
        self._emit(
            ctx,
            "LOT_REGISTERED",
            lot=lot,
            to_status=LotStatus.REGISTERED,
            data={
                "product": lot.product,
                "origin": lot.origin,
                "quantity_kg": lot.quantity_kg,
                "harvest_date": lot.harvest_date,
                "processor": lot.processor,
            },
        )

    def _record_processing(self, ctx: CallContext, args: dict[str, Any]) -> None:
        self._require_role(ctx, Role.PROCESSOR)
        parsed = parse_args(
            args,
            {"lot_id": lot_id_field, "description": note_text},
            {
                "carrier": address_field,
                "document_hash": sha256_field,
            },
        )
        lot = self._open_lot(parsed["lot_id"])
        self._require_next(lot, LotStatus.PROCESSED)
        self._require_designated_actor(lot.processor, ctx, "beneficiador")

        carrier = self._resolve_designated_actor(parsed.get("carrier"), Role.CARRIER)
        lot.carrier = carrier

        self._attach(lot, ctx, parsed.get("document_hash"), "Laudo de beneficiamento")
        self._advance(
            ctx,
            lot,
            LotStatus.PROCESSED,
            "LOT_PROCESSED",
            {
                "description": parsed["description"],
                "carrier": lot.carrier,
            },
        )

    def _start_transport(self, ctx: CallContext, args: dict[str, Any]) -> None:
        self._require_role(ctx, Role.CARRIER)
        parsed = parse_args(
            args,
            {
                "lot_id": lot_id_field,
                "recipient": address_field,
                "destination": place_text,
            },
        )
        lot = self._open_lot(parsed["lot_id"])
        self._require_next(lot, LotStatus.IN_TRANSIT)
        self._require_designated_actor(lot.carrier, ctx, "transportador")

        if Role.DISTRIBUTOR not in self.roles.get(parsed["recipient"], set()):
            raise ContractValidationError(
                "O destinatário informado não possui o perfil Distribuidor."
            )
        lot.recipient = parsed["recipient"]
        lot.destination = parsed["destination"]
        self._advance(
            ctx,
            lot,
            LotStatus.IN_TRANSIT,
            "TRANSPORT_STARTED",
            {"recipient": lot.recipient, "destination": lot.destination},
        )

    def _confirm_delivery(self, ctx: CallContext, args: dict[str, Any]) -> None:
        self._require_role(ctx, Role.DISTRIBUTOR)
        parsed = parse_args(args, {"lot_id": lot_id_field}, {"note": note_text})
        lot = self._open_lot(parsed["lot_id"])
        self._require_next(lot, LotStatus.DISTRIBUTED)
        if lot.recipient != ctx.sender:
            raise AccessDeniedError(
                "Somente o distribuidor designado no transporte pode confirmar "
                "o recebimento do lote."
            )
        self._advance(
            ctx,
            lot,
            LotStatus.DISTRIBUTED,
            "DELIVERY_CONFIRMED",
            {"note": parsed.get("note", "")},
        )

    def _finalize_lot(self, ctx: CallContext, args: dict[str, Any]) -> None:
        self._require_role(ctx, Role.DISTRIBUTOR)
        parsed = parse_args(args, {"lot_id": lot_id_field}, {"note": note_text})
        lot = self._open_lot(parsed["lot_id"])
        self._require_next(lot, LotStatus.FINALIZED)
        if lot.custodian != ctx.sender:
            raise AccessDeniedError(
                "Somente o responsável atual pelo lote pode finalizá-lo."
            )
        self._advance(
            ctx,
            lot,
            LotStatus.FINALIZED,
            "LOT_FINALIZED",
            {"note": parsed.get("note", "")},
        )

    def _attach_document(self, ctx: CallContext, args: dict[str, Any]) -> None:
        parsed = parse_args(
            args,
            {
                "lot_id": lot_id_field,
                "document_hash": sha256_field,
                "description": text_field(3, 120),
            },
        )
        lot = self._open_lot(parsed["lot_id"])
        if lot.custodian != ctx.sender:
            raise AccessDeniedError(
                "Somente o responsável atual pelo lote pode anexar documentos."
            )
        if any(doc["hash"] == parsed["document_hash"] for doc in lot.documents):
            raise ContractValidationError("Este documento já está registrado no lote.")
        self._attach(lot, ctx, parsed["document_hash"], parsed["description"])
        lot.updated_at = ctx.timestamp
        self._emit(
            ctx,
            "DOCUMENT_ATTACHED",
            lot=lot,
            data={
                "hash": parsed["document_hash"],
                "description": parsed["description"],
            },
        )

    # ------------------------------------------------------------------
    # Read-only queries
    # ------------------------------------------------------------------
    def get_lot(self, lot_id: str) -> Lot:
        """Return a lot or raise :class:`LotNotFoundError`."""
        lot = self.lots.get(lot_id)
        if lot is None:
            raise LotNotFoundError(f"O lote {lot_id} não existe no contrato.")
        return lot

    def list_lots(self, status: str | None = None) -> list[Lot]:
        """Return the lots ordered by identifier, optionally filtered by status."""
        lots = sorted(self.lots.values(), key=lambda lot: lot.lot_id)
        if status:
            lots = [lot for lot in lots if lot.status.value == status]
        return lots

    def roles_of(self, account: str) -> list[Role]:
        """Return the roles granted to ``account``."""
        return sorted(self.roles.get(account, set()), key=lambda role: role.value)

    def verify_document(self, lot_id: str, digest: str) -> dict[str, Any] | None:
        """Return the registered document of a lot with the given hash, if any."""
        lot = self.get_lot(lot_id)
        for document in lot.documents:
            if document["hash"] == digest.lower():
                return document
        return None

    def summary(self) -> dict[str, Any]:
        """Return the public description of the deployed contract."""
        counts = {status.value: 0 for status in LotStatus}
        for lot in self.lots.values():
            counts[lot.status.value] += 1
        return {
            "name": CONTRACT_NAME,
            "address": self.address,
            "admin": self.admin,
            "allowed_products": list(self.allowed_products),
            "deployed_at": self.deployed_at,
            "deploy_tx_hash": self.deploy_tx_hash,
            "lot_count": len(self.lots),
            "lots_by_status": counts,
            "methods": list(self._methods),
            "roles": {
                account: [role.value for role in self.roles_of(account)]
                for account in sorted(self.roles)
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _product_field(self, name: str, value: Any) -> str:
        cleaned = product_text(name, value)
        for product in self.allowed_products:
            if fold(product) == fold(cleaned):
                return product
        raise ContractValidationError(
            "Produto não permitido. Produtos aceitos: "
            f"{', '.join(self.allowed_products)}."
        )

    def _require_admin(self, ctx: CallContext) -> None:
        if ctx.sender != self.admin:
            raise AccessDeniedError(
                "Somente o administrador do contrato pode gerenciar perfis."
            )

    def _require_role(self, ctx: CallContext, role: Role) -> None:
        if role not in self.roles.get(ctx.sender, set()):
            raise AccessDeniedError(
                f"A carteira não possui o perfil {ROLE_LABELS[role.value]}, "
                "necessário para esta operação."
            )

    def _resolve_designated_actor(self, account: str | None, role: Role) -> str:
        """Validate an explicitly designated actor or infer the only eligible one."""
        label = ROLE_LABELS[role.value]
        if account is not None:
            if role not in self.roles.get(account, set()):
                raise ContractValidationError(
                    f"A carteira designada não possui o perfil {label}."
                )
            return account

        candidates = sorted(
            actor for actor, roles in self.roles.items() if role in roles
        )
        if len(candidates) == 1:
            return candidates[0]
        if not candidates:
            raise ContractValidationError(
                f"Não há nenhuma carteira com o perfil {label} disponível."
            )
        raise ContractValidationError(
            f"Há mais de uma carteira com o perfil {label}. "
            "Informe explicitamente quem será o responsável por esta etapa."
        )

    @staticmethod
    def _require_designated_actor(
        designated: str | None, ctx: CallContext, actor_label: str
    ) -> None:
        """Ensure the caller is the actor previously designated for the lot."""
        if designated != ctx.sender:
            raise AccessDeniedError(
                f"Somente o {actor_label} designado para este lote pode executar "
                "esta operação."
            )

    def _open_lot(self, lot_id: str) -> Lot:
        """Return an existing lot that is not finalized."""
        lot = self.get_lot(lot_id)
        if lot.status is LotStatus.FINALIZED:
            raise LotFinalizedError(
                f"O lote {lot_id} está FINALIZADO e não aceita novas alterações."
            )
        return lot

    @staticmethod
    def _require_next(lot: Lot, target: LotStatus) -> None:
        """Ensure ``target`` is exactly the stage that follows the current one."""
        expected = NEXT_STATUS[lot.status]
        if expected is not target:
            raise InvalidTransitionError(
                "Transição inválida: "
                f"{STATUS_LABELS[lot.status.value]} para "
                f"{STATUS_LABELS[target.value]}. "
                f"A próxima etapa permitida é {STATUS_LABELS[expected.value]}.",
                {"current": lot.status.value, "requested": target.value},
            )

    def _advance(
        self,
        ctx: CallContext,
        lot: Lot,
        target: LotStatus,
        event_name: str,
        data: dict[str, Any],
    ) -> None:
        previous = lot.status
        lot.status = target
        lot.custodian = ctx.sender
        lot.updated_at = ctx.timestamp
        self._emit(
            ctx, event_name, lot=lot, from_status=previous, to_status=target, data=data
        )

    @staticmethod
    def _attach(
        lot: Lot, ctx: CallContext, digest: str | None, description: str
    ) -> None:
        if not digest:
            return
        lot.documents.append(
            {
                "hash": digest,
                "description": description,
                "added_by": ctx.sender,
                "timestamp": ctx.timestamp,
                "tx_hash": ctx.tx_hash,
            }
        )

    def _emit(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        ctx: CallContext,
        name: str,
        lot: Lot | None = None,
        from_status: LotStatus | None = None,
        to_status: LotStatus | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        event = ContractEvent(
            name=name,
            actor=ctx.sender,
            timestamp=ctx.timestamp,
            tx_hash=ctx.tx_hash,
            lot_id=lot.lot_id if lot else None,
            from_status=from_status.value if from_status else None,
            to_status=to_status.value if to_status else None,
            data=data or {},
        )
        self.events.append(event)
        if lot is not None:
            lot.history.append(event)


def _products_field(name: str, value: Any) -> tuple[str, ...]:
    """Validate the list of products accepted by the contract."""
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_PRODUCTS:
        raise ContractValidationError(
            f"O campo '{name}' deve ser uma lista com 1 a {MAX_PRODUCTS} produtos."
        )
    products = [product_text(name, item) for item in value]
    if len({fold(item) for item in products}) != len(products):
        raise ContractValidationError(f"O campo '{name}' contém produtos repetidos.")
    return tuple(products)