"""File persistence for the chain and for the rejected operations log."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from ecoorigem.errors import EcoOrigemError

MAX_REJECTIONS_KEPT = 500


class StorageError(EcoOrigemError):
    """The stored ledger cannot be read."""

    code = "STORAGE_ERROR"
    http_status = 500


class LedgerStore:
    """Stores the chain as a JSON document and rejections as JSON lines."""

    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)
        self.ledger_path = self.directory / "ledger.json"
        self.rejections_path = self.directory / "rejections.jsonl"

    def load_chain(self) -> dict[str, Any] | None:
        """Return the stored chain, or ``None`` when nothing was saved yet."""
        if not self.ledger_path.exists():
            return None
        try:
            return json.loads(self.ledger_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise StorageError(
                f"O arquivo da blockchain não pôde ser lido: {self.ledger_path}."
            ) from error

    def save_chain(self, data: dict[str, Any]) -> None:
        """Write the chain atomically so a crash never leaves a partial file."""
        self.directory.mkdir(parents=True, exist_ok=True)
        descriptor, temp_name = tempfile.mkstemp(dir=self.directory, suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.ledger_path)
        except BaseException:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
            raise

    def append_rejection(self, entry: dict[str, Any]) -> None:
        """Append a rejected operation to the log."""
        self.directory.mkdir(parents=True, exist_ok=True)
        with self.rejections_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def load_rejections(self) -> list[dict[str, Any]]:
        """Return the most recent rejected operations, oldest first."""
        if not self.rejections_path.exists():
            return []
        entries: list[dict[str, Any]] = []
        for line in self.rejections_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except ValueError:
                    continue
        return entries[-MAX_REJECTIONS_KEPT:]
