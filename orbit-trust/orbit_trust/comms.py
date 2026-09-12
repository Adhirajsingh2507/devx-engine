"""Communication simulation sandbox (handoff doc 07).

Scripted packets only. No real satellite, radio network or external connector;
`report_execution` is a simulation record, never proof of a command. Timing
feasibility uses supplied delays only, never Groq/HTTP speed.
"""

from __future__ import annotations

from typing import Optional

from .models import parse_utc

# packet states (doc 07)
DRAFT = "draft"
AUTHORIZED = "authorized_for_simulation"
WAITING = "waiting_for_contact"
SENT = "sent"
ACKNOWLEDGED = "acknowledged"
EXECUTION_REPORTED = "execution_reported"
EXPIRED = "expired"
FAILED = "failed"
CANCELLED = "cancelled"

REJECT_SEND = "reject_send"
REJECT_AUTH = "reject_authorization"


def timing_feasibility(scn: dict) -> dict:
    """Does the full uplink + ack + action-lead chain fit the supplied windows?

    Returns {status, modeled_completion}. status is fits_supplied_window,
    timing_unknown (any input missing) or does_not_fit. real_transmission is
    always False."""
    required = ("contact_start", "contact_end", "action_deadline", "uplink_s", "ack_allowance_s", "action_lead_s")
    if any(scn.get(k) is None for k in required):
        return {"timing_status": "timing_unknown", "modeled_completion": None, "real_transmission_performed": False}

    from datetime import timedelta

    now = parse_utc(scn["now"])
    contact_start = parse_utc(scn["contact_start"])
    contact_end = parse_utc(scn["contact_end"])
    action_deadline = parse_utc(scn["action_deadline"])

    send_at = max(now, contact_start)
    uplink_end = send_at + timedelta(seconds=scn["uplink_s"])
    ack_at = uplink_end + timedelta(seconds=scn["ack_allowance_s"])
    completion = ack_at + timedelta(seconds=scn["action_lead_s"])

    fits = uplink_end <= contact_end and ack_at <= contact_end and completion <= action_deadline
    return {
        "timing_status": "fits_supplied_window" if fits else "does_not_fit",
        "modeled_completion": completion.strftime("%Y-%m-%dT%H:%M:%SZ") if fits else None,
        "real_transmission_performed": False,
    }


class Packet:
    """A single simulated command packet and its state transitions."""

    def __init__(self, scn: dict):
        self.state = DRAFT
        self.contact_start = parse_utc(scn["contact_start"]) if scn.get("contact_start") else None
        self.contact_end = parse_utc(scn["contact_end"]) if scn.get("contact_end") else None
        self.expires_at = parse_utc(scn["packet_expires_at"])

    def _expired(self, at_iso: str) -> bool:
        return parse_utc(at_iso) >= self.expires_at  # expiration is inclusive (doc 07)

    def authorize(self, at_iso: str, *, comparison_stale: bool = False) -> str:
        if comparison_stale:
            return REJECT_AUTH  # a stale packet cannot be authorized
        if self._expired(at_iso):
            self.state = EXPIRED
            return self.state
        self.state = AUTHORIZED
        return self.state

    def send(self, at_iso: str) -> str:
        if self._expired(at_iso):
            self.state = EXPIRED
            return self.state
        at = parse_utc(at_iso)
        if self.contact_start is None or not (self.contact_start <= at <= self.contact_end):
            return REJECT_SEND  # outside the supplied contact window; state unchanged
        self.state = SENT
        return self.state

    def acknowledge(self, at_iso: str) -> str:
        if self.state == SENT:
            self.state = ACKNOWLEDGED
        return self.state

    def report_execution(self, at_iso: str) -> str:
        if self.state == ACKNOWLEDGED:  # only via a valid ack -> execution sequence
            self.state = EXECUTION_REPORTED
        return self.state

    def ack_timeout(self) -> str:
        if self.state == SENT:  # sent with no acknowledgement becomes failed
            self.state = FAILED
        return self.state

    def cancel(self) -> str:
        if self.state in (DRAFT, AUTHORIZED, WAITING):
            self.state = CANCELLED
        return self.state
