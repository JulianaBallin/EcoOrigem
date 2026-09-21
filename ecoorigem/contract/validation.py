"""Argument validators used by the smart contract.

Every validator receives the raw value and returns the normalized one, or
raises :class:`ContractValidationError` with a message in Portuguese.
"""

from __future__ import annotations

import math
import re
import unicodedata
from datetime import date, datetime, timezone
from typing import Any, Callable

from ecoorigem.blockchain.wallet import ADDRESS_PATTERN
from ecoorigem.contract.types import Role
from ecoorigem.errors import ContractValidationError

LOT_ID_PATTERN = re.compile(r"^LOT-\d{4,}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
MIN_HARVEST_DATE = date(2000, 1, 1)
MAX_QUANTITY_KG = 100_000.0

Validator = Callable[[str, Any], Any]


def fold(text: str) -> str:
    """Lowercase ``text`` and remove accents, for tolerant comparisons."""
    decomposed = unicodedata.normalize("NFKD", text.strip().casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def text_field(minimum: int, maximum: int) -> Validator:
    """Build a validator for free text with length limits."""

    def validate(name: str, value: Any) -> str:
        if not isinstance(value, str):
            raise ContractValidationError(f"O campo '{name}' deve ser um texto.")
        cleaned = " ".join(value.split())
        if any(unicodedata.category(char) == "Cc" for char in value.replace("\n", " ")):
            raise ContractValidationError(
                f"O campo '{name}' contém caracteres inválidos."
            )
        if not minimum <= len(cleaned) <= maximum:
            raise ContractValidationError(
                f"O campo '{name}' deve ter entre {minimum} e {maximum} caracteres."
            )
        return cleaned

    return validate


def address_field(name: str, value: Any) -> str:
    """Validate an account address."""
    if not isinstance(value, str) or not ADDRESS_PATTERN.match(value):
        raise ContractValidationError(f"O campo '{name}' deve ser um endereço válido.")
    return value


def role_field(name: str, value: Any) -> Role:
    """Validate a role name."""
    try:
        return Role(value)
    except ValueError as error:
        allowed = ", ".join(role.value for role in Role)
        raise ContractValidationError(
            f"O campo '{name}' deve ser um dos perfis: {allowed}."
        ) from error


def lot_id_field(name: str, value: Any) -> str:
    """Validate the format of a lot identifier."""
    if not isinstance(value, str) or not LOT_ID_PATTERN.match(value):
        raise ContractValidationError(
            f"O campo '{name}' deve seguir o formato LOT-0001."
        )
    return value


def sha256_field(name: str, value: Any) -> str:
    """Validate a SHA-256 digest in lowercase hexadecimal."""
    if not isinstance(value, str) or not SHA256_PATTERN.match(value.lower()):
        raise ContractValidationError(
            f"O campo '{name}' deve ser um hash SHA-256 com 64 caracteres hexadecimais."
        )
    return value.lower()


def quantity_field(name: str, value: Any) -> float:
    """Validate a positive quantity in kilograms."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractValidationError(f"O campo '{name}' deve ser numérico.")
    if not math.isfinite(value) or value <= 0:
        raise ContractValidationError(f"O campo '{name}' deve ser maior que zero.")
    if value > MAX_QUANTITY_KG:
        raise ContractValidationError(
            f"O campo '{name}' excede o limite de {MAX_QUANTITY_KG:,.0f} kg por lote."
        )
    return round(float(value), 3)


def harvest_date_field(name: str, value: Any, today: date) -> str:
    """Validate an ISO date that is neither in the future nor too old."""
    if not isinstance(value, str):
        raise ContractValidationError(f"O campo '{name}' deve ser uma data AAAA-MM-DD.")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as error:
        raise ContractValidationError(
            f"O campo '{name}' deve ser uma data válida no formato AAAA-MM-DD."
        ) from error
    if parsed > today:
        raise ContractValidationError(f"O campo '{name}' não pode estar no futuro.")
    if parsed < MIN_HARVEST_DATE:
        raise ContractValidationError(f"O campo '{name}' é anterior a 2000-01-01.")
    return parsed.isoformat()


def date_of(timestamp_ms: int) -> date:
    """Return the UTC calendar date of a millisecond timestamp."""
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).date()


def parse_args(
    args: dict[str, Any],
    required: dict[str, Validator],
    optional: dict[str, Validator] | None = None,
) -> dict[str, Any]:
    """Validate ``args`` against the given field validators.

    Unknown fields are rejected so typos never pass silently.
    """
    optional = optional or {}
    unknown = sorted(set(args) - set(required) - set(optional))
    if unknown:
        raise ContractValidationError(
            f"Campos desconhecidos: {', '.join(unknown)}.", {"fields": unknown}
        )
    parsed: dict[str, Any] = {}
    for name, validator in required.items():
        if name not in args:
            raise ContractValidationError(
                f"Campo obrigatório ausente: {name}.", {"field": name}
            )
        parsed[name] = validator(name, args[name])
    for name, validator in optional.items():
        if name in args and args[name] not in (None, ""):
            parsed[name] = validator(name, args[name])
    return parsed
