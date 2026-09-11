"""Domain validation and import classification (handoff doc 05).

Two layers: structural (Pydantic `Record`, => schema_422) then domain rules that
JSON Schema cannot express. Per doc 05 an import distinguishes:
 - reject: structural (422) or invalid association (e.g. same object pair)
 - unsupported (retained): structurally valid report whose encounter cannot be
   computed (e.g. invalid covariance) — kept in the ledger with a finding
 - accept: valid record
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pydantic import TypeAdapter, ValidationError

from . import numerics
from .models import Record, Report

_REC = TypeAdapter(Record)

ACCEPT = "accept"
REJECT = "reject"
UNSUPPORTED = "unsupported"  # retained record, calculation unsupported


@dataclass
class RecordOutcome:
    status: str
    reason: Optional[str]
    kind: Optional[str]
    model: object | None


def classify_record(obj: dict) -> RecordOutcome:
    try:
        model = _REC.validate_python(obj)
    except ValidationError:
        return RecordOutcome(REJECT, "schema_422", None, None)

    kind = obj.get("bundle_kind")
    if isinstance(model, Report):
        return _classify_report(model, kind)
    # candidate_set / economic / reentry / communication: structural ok here;
    # their computational evaluators (M3/M4) apply their own domain rules.
    return RecordOutcome(ACCEPT, None, kind, model)


def _classify_report(r: Report, kind: str) -> RecordOutcome:
    if r.primary_object_id == r.secondary_object_id:
        return RecordOutcome(REJECT, "domain_pair_mismatch", kind, r)

    enc = r.encounter
    if enc is None:
        # Missing encounter is allowed for reported-risk audit (doc 05); the
        # missing-evidence finding is attached during assessment.
        return RecordOutcome(ACCEPT, None, kind, r)

    # Encounter object IDs must match the report pair and stay distinct.
    if {enc.primary.object_id, enc.secondary.object_id} != {r.primary_object_id, r.secondary_object_id}:
        return RecordOutcome(REJECT, "domain_pair_mismatch", kind, r)
    if enc.primary.object_id == enc.secondary.object_id:
        return RecordOutcome(REJECT, "domain_pair_mismatch", kind, r)

    # interval must be ordered (doc 05)
    if enc.interval_start_offset_s >= enc.interval_end_offset_s:
        return RecordOutcome(REJECT, "domain_invalid_interval", kind, r)

    # Covariance validity -> unsupported calculation, but the report is retained.
    for obj in (enc.primary, enc.secondary):
        ok, reason = numerics.covariance_status(obj.position_covariance_m2)
        if not ok:
            return RecordOutcome(UNSUPPORTED, reason, kind, r)

    return RecordOutcome(ACCEPT, None, kind, r)


def import_summary(objs: list[dict]) -> dict:
    """Per-record acceptance/rejection report (doc 05). Deduplication and
    source-conflict detection (which need the workspace ledger) arrive with the
    storage layer in M1; this covers structural + domain classification."""
    accepted = rejected = unsupported = 0
    errors = []
    for i, obj in enumerate(objs):
        outcome = classify_record(obj)
        if outcome.status == ACCEPT:
            accepted += 1
        elif outcome.status == UNSUPPORTED:
            unsupported += 1
            errors.append({"index": i, "status": UNSUPPORTED, "reason": outcome.reason})
        else:
            rejected += 1
            errors.append({"index": i, "status": REJECT, "reason": outcome.reason})
    return {
        "accepted": accepted,
        "rejected": rejected,
        "unsupported": unsupported,
        "errors": errors,
    }
