"""Hash helpers: SHA-256 and canonical JSON serialization."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Serialize ``value`` to a deterministic JSON string.

    Keys are sorted and no whitespace is emitted, so the same data always
    produces the same bytes and therefore the same hash on every machine.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: str | bytes) -> str:
    """Return the SHA-256 digest of ``data`` as a lowercase hex string."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()
