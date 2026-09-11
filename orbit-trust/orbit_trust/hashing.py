"""Canonical digests (handoff doc 04).

Normalize over sorted-key, compact, UTF-8 JSON with finite numbers and canonical
UTC timestamps. The original-file SHA-256 is kept separately (raw_sha256). Two
different serializations of the same content must hash identically.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any


def _check_finite(obj: Any) -> None:
    if isinstance(obj, float) and not math.isfinite(obj):
        raise ValueError("non_finite_number_in_digest_input")
    if isinstance(obj, dict):
        for v in obj.values():
            _check_finite(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _check_finite(v)


def canonical_json(obj: Any) -> str:
    _check_finite(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_digest(obj: Any) -> str:
    """SHA-256 over the canonical JSON form (key-order independent)."""
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def raw_sha256(text: str) -> str:
    """SHA-256 of the original uploaded bytes, kept separate from the canonical digest."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
