"""Deadline-aware review policy `demo-2.0` (handoff doc 06).

Illustrative mission policy, not universal operational instruction. Thresholds:
review theta = 1e-4, immediate-review slack = 3600 s. Urgency is deterministic
and host-owned; the LLM never sets it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from .models import parse_utc

POLICY_VERSION = "demo-2.0"
REVIEW_THRESHOLD = 1e-4
IMMEDIATE_SLACK_S = 3600

# Lower rank = more urgent.
_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def proposed_urgency(
    now: datetime,
    review_deadline: Optional[datetime],
    review_required: bool,
    *,
    immediate_slack_s: int = IMMEDIATE_SLACK_S,
) -> str:
    """P0-P3 per doc 06. `review_required` folds in material concern OR
    missing information needed to classify (both require review)."""
    if not review_required:
        return "P3"
    if review_deadline is None:
        return "P1"  # required review, deadline unknown
    if now > review_deadline:
        return "P0"  # overdue
    slack = (review_deadline - now).total_seconds()
    if slack <= immediate_slack_s:  # at exactly the deadline slack==0 -> P1
        return "P1"
    return "P2"


def more_urgent(a: str, b: str) -> str:
    return a if _RANK[a] <= _RANK[b] else b


def effective_urgency(
    proposed: str,
    *,
    unacknowledged_floor: Optional[str],
    latest_assessment_acknowledged: bool,
) -> str:
    """An automatic downgrade cannot silently clear an unacknowledged P0/P1
    floor (doc 06). The floor holds until the latest assessment is
    acknowledged; then current policy may allow the lower urgency."""
    if unacknowledged_floor is None or latest_assessment_acknowledged:
        return proposed
    return more_urgent(unacknowledged_floor, proposed)


def review_deadline(latest_command_at: str, review_allowance_s: float) -> datetime:
    """Latest feasible command opportunity minus the review/coordination
    allowance (doc 06). Never invented from TCA alone."""
    from datetime import timedelta

    return parse_utc(latest_command_at) - timedelta(seconds=review_allowance_s)
