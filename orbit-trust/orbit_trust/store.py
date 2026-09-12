"""In-memory, workspace-scoped store (docs 05/19).

This is the ONLY place that holds state. The Supabase-backed store (docs 14/19)
re-implements the same shape later; `service.py` is the sole caller, so the seam
lives here. Not durable across restarts and not safe across multiple worker
processes.

ponytail: global process lock + single-process dict. Fine for the synthetic
demo; swap for the Supabase transactional store (per-workspace rows, atomic
RPCs) when persistence lands. Idempotency likewise moves to a DB table then
(doc 05 forbids relying on process memory on Vercel).
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .ledger import ReportLedger

LOCK = threading.RLock()

_IDEMPOTENCY_TTL_S = 24 * 3600


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class StoredReport:
    """Immutable source record kept for a case's history (doc 05)."""

    report_id: str
    source_name: str
    source_revision: str
    created_at: str
    reported_tca: str
    digest: str
    outcome: str          # ledger outcome, or "unsupported" for a retained record
    body: dict


@dataclass
class Case:
    case_id: str
    event_key: str
    pair: tuple                 # sorted (object_a, object_b)
    reported_tca: str
    state: str = "new"
    revision: int = 0
    latest_assessment_id: Optional[str] = None
    assessment: Optional[dict] = None
    # urgency bookkeeping (doc 06): an automatic downgrade cannot silently clear
    # an unacknowledged P0/P1 floor until the latest assessment is acknowledged.
    unacknowledged_floor: Optional[str] = None
    latest_assessment_acknowledged: bool = True
    assignment: Optional[str] = None
    current_report_created_at: Optional[str] = None
    reports: list = field(default_factory=list)   # list[StoredReport], append-only

    def effective_urgency(self) -> str:
        from . import policy
        proposed = (self.assessment or {}).get("proposed_urgency", "P3")
        return policy.effective_urgency(
            proposed,
            unacknowledged_floor=self.unacknowledged_floor,
            latest_assessment_acknowledged=self.latest_assessment_acknowledged,
        )

    def deadline(self) -> Optional[str]:
        return (self.assessment or {}).get("deadline")

    def material_concern(self) -> bool:
        return bool((self.assessment or {}).get("material_concern"))

    def unresolved_required_review(self) -> bool:
        a = self.assessment or {}
        return bool(a.get("review_required")) and not self.latest_assessment_acknowledged


@dataclass
class Workspace:
    workspace_id: str
    owner_id: str
    mode: str
    revision: int = 0            # queue/data revision: bumped on any case change
    created_at: str = ""
    members: set = field(default_factory=set)
    cases: dict = field(default_factory=dict)          # event_key -> Case
    ledger: ReportLedger = field(default_factory=ReportLedger)
    assessments: dict = field(default_factory=dict)    # assessment_id -> dict
    audit: list = field(default_factory=list)          # list[dict], append-only
    idempotency: dict = field(default_factory=dict)    # key -> (digest, result, expiry)

    def bump(self) -> None:
        self.revision += 1

    def record_audit(self, actor: str, event_type: str, entity: str, summary: dict) -> None:
        self.audit.append({
            "sequence": len(self.audit) + 1,
            "actor": actor,
            "event_type": event_type,
            "entity": entity,
            "summary": summary,
            "at": now_iso(),
        })


# workspace_id -> Workspace
_WORKSPACES: dict[str, Workspace] = {}
# creation-time idempotency keyed by (owner_id, key); per-workspace idempotency
# lives on the Workspace itself.
_CREATE_IDEMPOTENCY: dict[tuple, tuple] = {}


def create_workspace(owner_id: str, mode: str) -> Workspace:
    ws = Workspace(workspace_id=new_id("ws"), owner_id=owner_id, mode=mode, created_at=now_iso())
    ws.members.add(owner_id)
    _WORKSPACES[ws.workspace_id] = ws
    return ws


def get_workspace(workspace_id: str) -> Optional[Workspace]:
    return _WORKSPACES.get(workspace_id)


def delete_workspace(workspace_id: str) -> None:
    _WORKSPACES.pop(workspace_id, None)


def _purge_expired(table: dict) -> None:
    now = time.time()
    for k in [k for k, v in table.items() if v[2] < now]:
        table.pop(k, None)


def idempotent(table: dict, key: str, digest: str, produce):
    """Same key+digest returns the original result; a different digest is a
    conflict; otherwise the result is produced, stored for 24h and returned
    (doc 05). Raises KeyError('conflict') on a digest mismatch."""
    _purge_expired(table)
    rec = table.get(key)
    if rec is not None:
        stored_digest, result, _ = rec
        if stored_digest != digest:
            raise KeyError("conflict")
        return result
    result = produce()
    table[key] = (digest, result, time.time() + _IDEMPOTENCY_TTL_S)
    return result


def create_idempotency_table() -> dict:
    return _CREATE_IDEMPOTENCY
