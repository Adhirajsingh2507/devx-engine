"""Decimal money helpers (handoff doc 08).

Use decimal arithmetic; round only the final display. Input monetary values are
decimal strings; probabilities are parsed through their decimal text (never a
binary-float rounding step before multiplying money). `dec(str(x))` recovers the
exact intended decimal for a JSON float via its shortest round-tripping repr.
"""

from __future__ import annotations

from decimal import Decimal


def dec(value) -> Decimal:
    """Coerce a Decimal / decimal-string / JSON number to Decimal without
    introducing binary-float error."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def fmt(d: Decimal) -> str:
    """Fixed-point string with trailing zeros stripped (e.g. Decimal('100000.0000')
    -> '100000', Decimal('-21000') -> '-21000')."""
    return format(d.normalize(), "f")
