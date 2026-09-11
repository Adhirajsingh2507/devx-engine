"""Fleet comparison of supplied response candidates (handoff doc 07).

Evaluate every unordered pair for the baseline and each supplied alternative
over the supplied short-encounter interval, apply the supplied policy threshold,
and derive a candidate disposition. Pairwise probabilities are NOT combined into
a single "fleet collision" number (no joint event model). Candidates are
"preferred among supplied options", never globally optimal.
"""

from __future__ import annotations

from itertools import combinations

from . import numerics

BLOCKED = "blocked_by_demo_policy"
INCOMPLETE = "review_required_incomplete"
PASSES = "passes_demo_checks"


def _pair_result(a: dict, b: dict, cset: dict, threshold: float) -> dict:
    enc = {
        "primary": a,
        "secondary": b,
        "domain": cset["domain"],
        "interval_start_offset_s": cset["interval_start_offset_s"],
        "interval_end_offset_s": cset["interval_end_offset_s"],
    }
    ev = numerics.evaluate_encounter(enc)
    supported = ev["status"] == "supported"
    pc = ev["pc"] if supported else None
    return {
        "pair": [a["object_id"], b["object_id"]],
        "status": ev["status"],
        "tca_offset_s": ev.get("tca_offset_s"),
        "miss_distance_m": ev.get("miss_distance_m"),
        "pc": pc,
        "threshold_exceeded": bool(supported and pc is not None and pc >= threshold),
    }


def _object_set_for(cset: dict, candidate: dict | None) -> list[dict]:
    """Baseline objects, or the objects with the selected object's state replaced
    by the candidate's supplied state (doc 07: alternatives replace only that
    object)."""
    if candidate is None:
        return list(cset["objects"])
    selected = cset["selected_object_id"]
    replacement = candidate["selected_object_state"]
    return [replacement if o["object_id"] == selected else o for o in cset["objects"]]


def _disposition(pairs: list[dict], feasible) -> str:
    if feasible is False:  # supplied hard feasibility constraint fails
        return BLOCKED
    if any(p["threshold_exceeded"] for p in pairs):
        return BLOCKED
    if any(p["status"] != "supported" for p in pairs):
        return INCOMPLETE  # a required pair unsupported/incomplete is never a pass
    return PASSES


def compare(cset: dict) -> dict:
    threshold = cset["policy_threshold"]

    def eval_objects(objs: list[dict], feasible) -> list:
        pairs = [_pair_result(a, b, cset, threshold) for a, b in combinations(objs, 2)]
        return pairs, _disposition(pairs, feasible)

    results = []
    base_pairs, base_disp = eval_objects(_object_set_for(cset, None), None)
    results.append({"candidate_id": "baseline", "pairs": base_pairs, "disposition": base_disp})

    passing = []
    for cand in cset["alternatives"]:
        objs = _object_set_for(cset, cand)
        pairs, disp = eval_objects(objs, cand.get("feasible"))
        results.append({"candidate_id": cand["candidate_id"], "pairs": pairs, "disposition": disp})
        if disp == PASSES:
            passing.append(cand)

    # Preferred among passing alternatives: delta_v asc, then response cost, then
    # id. Unknown cost/delta-v sorts last (doc 07).
    def sort_key(c: dict):
        dv = c.get("delta_v_m_s")
        cost = c.get("response_cost")
        cost_amount = float(cost["amount"]) if cost else float("inf")
        return (
            dv if dv is not None else float("inf"),
            cost_amount,
            c["candidate_id"],
        )

    preferred = sorted(passing, key=sort_key)[0]["candidate_id"] if passing else None

    interval_s = cset["interval_end_offset_s"] - cset["interval_start_offset_s"]
    coverage = (
        f"All {len(cset['objects'])} supplied objects assessed over this "
        f"{interval_s:g}-second synthetic encounter segment."
    )
    return {
        "candidate_results": results,
        "preferred_among_passing_alternatives": preferred,
        "coverage_label": coverage,
    }
