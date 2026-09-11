"""Conditional loss and expected-loss change (handoff doc 08).

Conditional loss L is the sum of included monetary terms in ONE currency.
Single-event expected loss is Pc * L when Pc applies to the same event.
Net benefit of response = (Pc_before - Pc_after)*L - response_cost for a fixed
comparable L, or Pc_before*L_before - Pc_after*L_after - response_cost otherwise.

Unknown probability or loss -> unavailable, never zero. Mixed-currency
arithmetic, negative probabilities and negative declared costs are rejected. A
negative net benefit is displayed, not clipped, and never cancels a required
review.
"""

from __future__ import annotations

from decimal import Decimal

from .money import dec, fmt

UNAVAILABLE = "domain_result_unavailable"
CURRENCY_MISMATCH = "domain_currency_mismatch"
INVALID = "domain_invalid_value"


def _sum_loss(items: list[dict]) -> tuple[Decimal, str]:
    currencies = {it["money"]["currency"] for it in items}
    if len(currencies) != 1:
        raise ValueError(CURRENCY_MISMATCH)
    total = sum((dec(it["money"]["amount"]) for it in items), Decimal(0))
    return total, currencies.pop()


def evaluate(scn: dict) -> dict:
    """Evaluate an EconomicScenario dict. Probabilities should be Decimal or
    JSON numbers (parse the source with parse_float=Decimal for exactness)."""
    before, after = scn["before_probability"], scn["after_probability"]
    if before is None or after is None:
        return {"status": "unavailable", "reason": UNAVAILABLE}

    try:
        loss_before, cur_b = _sum_loss(scn["loss_items_before"])
        loss_after, cur_a = _sum_loss(scn["loss_items_after"])
    except ValueError as exc:
        return {"status": "unavailable", "reason": str(exc)}

    cost = scn["response_cost"]
    cur_cost = cost["currency"]
    if not (cur_b == cur_a == cur_cost):
        return {"status": "unavailable", "reason": CURRENCY_MISMATCH}

    pc_before, pc_after = dec(before), dec(after)
    cost_amount = dec(cost["amount"])
    if pc_before < 0 or pc_after < 0 or cost_amount < 0:
        return {"status": "unavailable", "reason": INVALID}

    expected_before = pc_before * loss_before
    expected_after = pc_after * loss_after
    gross_reduction = expected_before - expected_after
    net_benefit = gross_reduction - cost_amount  # may be negative; displayed, not clipped

    return {
        "status": "available",
        "currency": cur_b,
        "loss_before": fmt(loss_before),
        "loss_after": fmt(loss_after),
        "expected_loss_before": fmt(expected_before),
        "expected_loss_after": fmt(expected_after),
        "gross_reduction": fmt(gross_reduction),
        "net_benefit": fmt(net_benefit),
    }
