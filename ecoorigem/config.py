"""Runtime settings read from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "sim"}


@dataclass(frozen=True)
class Settings:  # pylint: disable=too-many-instance-attributes
    """Configuration shared by the node, the web application and the CLI."""

    data_dir: Path
    difficulty: int
    auto_mine: bool
    lab_enabled: bool
    node_host: str
    node_port: int
    node_url: str
    web_host: str
    web_port: int
    demo_seed: str | None

    @property
    def node_dir(self) -> Path:
        """Directory that stores the chain of the local node."""
        return self.data_dir / "node"

    @property
    def keystore_path(self) -> Path:
        """File that stores the demonstration wallets."""
        return self.data_dir / "wallet" / "wallets.json"

    @classmethod
    def from_env(cls) -> "Settings":
        """Build the settings from ``ECOORIGEM_*`` environment variables."""
        node_host = os.environ.get("ECOORIGEM_NODE_HOST", "127.0.0.1")
        node_port = int(os.environ.get("ECOORIGEM_NODE_PORT", "8545"))
        return cls(
            data_dir=Path(os.environ.get("ECOORIGEM_DATA_DIR", "data")),
            difficulty=int(os.environ.get("ECOORIGEM_DIFFICULTY", "4")),
            auto_mine=_flag("ECOORIGEM_AUTO_MINE", True),
            lab_enabled=_flag("ECOORIGEM_LAB", True),
            node_host=node_host,
            node_port=node_port,
            node_url=os.environ.get(
                "ECOORIGEM_NODE_URL", f"http://127.0.0.1:{node_port}"
            ),
            web_host=os.environ.get("ECOORIGEM_WEB_HOST", "127.0.0.1"),
            web_port=int(os.environ.get("ECOORIGEM_WEB_PORT", "5000")),
            demo_seed=os.environ.get("ECOORIGEM_DEMO_SEED") or None,
        )
