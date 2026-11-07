"""Local keystore holding the demonstration wallets.

The keystore plays the role that MetaMask (or the unlocked accounts of a
development node) plays in a regular DApp: it keeps the private keys outside
of the node and signs transactions on behalf of the selected account.
The file is created with mode ``0600`` and must never be committed.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from ecoorigem.blockchain.wallet import Wallet


@dataclass(frozen=True)
class DemoProfile:
    """Description of a demonstration account."""

    label: str
    display_name: str
    description: str


DEMO_PROFILES: tuple[DemoProfile, ...] = (
    DemoProfile(
        "administrador",
        "Administrador",
        "Implanta o contrato e gerencia as permissões.",
    ),
    DemoProfile(
        "produtor",
        "Produtor",
        "Cooperativa que registra a origem e cria os lotes.",
    ),
    DemoProfile(
        "beneficiador",
        "Beneficiador",
        "Agroindústria que registra o beneficiamento.",
    ),
    DemoProfile(
        "transportador",
        "Transportador",
        "Empresa que registra o transporte do lote.",
    ),
    DemoProfile(
        "distribuidor",
        "Distribuidor",
        "Confirma o recebimento e finaliza a distribuição.",
    ),
    DemoProfile(
        "intruso",
        "Carteira sem permissão",
        "Conta sem perfil, usada para demonstrar a rejeição de acessos.",
    ),
)

PROFILE_BY_LABEL = {profile.label: profile for profile in DEMO_PROFILES}


class Keystore:
    """Persistent collection of wallets indexed by label."""

    def __init__(self, path: Path, wallets: dict[str, Wallet]) -> None:
        self.path = path
        self._wallets = wallets

    @classmethod
    def load_or_create(cls, path: Path, seed: str | None = None) -> "Keystore":
        """Load the keystore at ``path`` or create it with the demo profiles.

        When ``seed`` is given the keys are derived from it, which makes the
        addresses reproducible across machines. Without a seed every key is
        random.
        """
        path = Path(path)
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            wallets = {
                label: Wallet(label, private_key)
                for label, private_key in raw["wallets"].items()
            }
            return cls(path, wallets)
        wallets = {}
        for profile in DEMO_PROFILES:
            if seed:
                wallets[profile.label] = Wallet.from_seed(profile.label, seed)
            else:
                wallets[profile.label] = Wallet.generate(profile.label)
        keystore = cls(path, wallets)
        keystore.save()
        return keystore

    def save(self) -> None:
        """Write the keystore to disk with restrictive permissions."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "warning": "Chaves de demonstração. Não versionar nem reutilizar.",
            "wallets": {
                label: wallet.export_private_key()
                for label, wallet in self._wallets.items()
            },
        }
        descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        os.chmod(self.path, 0o600)

    def labels(self) -> list[str]:
        """Return the wallet labels in a stable order."""
        ordered = [p.label for p in DEMO_PROFILES if p.label in self._wallets]
        extra = sorted(label for label in self._wallets if label not in ordered)
        return ordered + extra

    def get(self, reference: str) -> Wallet | None:
        """Find a wallet by label or by address."""
        if reference in self._wallets:
            return self._wallets[reference]
        for wallet in self._wallets.values():
            if wallet.address == reference:
                return wallet
        return None

    def wallets(self) -> list[Wallet]:
        """Return all wallets in a stable order."""
        return [self._wallets[label] for label in self.labels()]
