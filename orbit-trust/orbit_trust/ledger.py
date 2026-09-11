"""Immutable report ledger: grouping, dedup and source-conflict (docs 05/19).

Pure in-memory model of report ingestion so the rules are unit-testable without
a database. The Supabase transaction in M1 enforces the same invariants
atomically (report uniqueness = workspace+case+source_name+source_revision+raw
digest; same revision + different body = retained conflict, never overwrite).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .hashing import canonical_digest
from .models import parse_utc

# outcome codes mirror report_update_cases.json expectations
DEDUP = "deduplicate_no_scientific_revision"
PRESERVE = "preserve_history_do_not_replace_current_source"
CONFLICT = "retain_both_mark_source_conflict"
REJECT_PAIR = "reject_association"
CURRENT = "accepted_current"


@dataclass
class _Entry:
    source_name: str
    source_revision: str
    digest: str
    created_at: str
    conflict: bool = False


@dataclass
class ReportLedger:
    pairs: dict = field(default_factory=dict)          # event_key -> frozenset object pair
    streams: dict = field(default_factory=dict)        # event_key -> list[_Entry]

    def ingest(self, report: dict) -> str:
        event_key = report["event_key"]
        pair = frozenset({report["primary_object_id"], report["secondary_object_id"]})

        # Never merge two providers' events by similar TCA/names; a reused event
        # key with a different object pair is rejected (doc 05).
        if event_key in self.pairs and self.pairs[event_key] != pair:
            return REJECT_PAIR
        self.pairs.setdefault(event_key, pair)

        stream = self.streams.setdefault(event_key, [])
        digest = canonical_digest(report)
        sn, sr = report["source_name"], report["source_revision"]

        for e in stream:
            if e.source_name == sn and e.source_revision == sr:
                if e.digest == digest:
                    return DEDUP  # identical report, no new scientific revision
                stream.append(_Entry(sn, sr, digest, report["created_at"], conflict=True))
                return CONFLICT  # same revision, different body -> retained conflict

        # New revision. Arrival order is not scientific recency: order by
        # creation time and preserve out-of-order arrivals (doc 05).
        same_source = [e for e in stream if e.source_name == sn]
        stream.append(_Entry(sn, sr, digest, report["created_at"]))
        if same_source:
            newest = max(parse_utc(e.created_at) for e in same_source)
            if parse_utc(report["created_at"]) < newest:
                return PRESERVE
        return CURRENT
