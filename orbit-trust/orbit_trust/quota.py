"""Run / token quotas for the bounded agent (doc 09).

A live provider run must reserve budget before it starts and reconcile actual
usage after. This guards spend and concurrency so one workspace (or a runaway
retry loop) cannot exhaust the demo's Groq allowance. Exceeding any limit raises
`QuotaError`, which the caller turns into the deterministic labeled fallback —
never a hard failure of the case review.

ponytail: process-global, in-memory, threading.Lock. The real system reserves
in the DB (doc 09) so limits hold across workers/restarts; swap `_STATE` for a
Supabase reservation row at N2. Daily counters reset on process date rollover
only — fine for a single-process demo.
"""

from __future__ import annotations

import os
import threading
from datetime import date


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "").strip() or default)
    except ValueError:
        return default


class Limits:
    """Resolved at call time so tests/env can override without reimport."""

    @property
    def max_concurrent(self) -> int:
        return _env_int("AGENT_MAX_CONCURRENT_RUNS", 2)

    @property
    def per_user_per_day(self) -> int:
        return _env_int("AGENT_MAX_RUNS_PER_USER_DAY", 50)

    @property
    def global_tokens_per_day(self) -> int:
        return _env_int("AGENT_MAX_TOKENS_DAY", 200_000)

    @property
    def max_tokens_per_run(self) -> int:
        return _env_int("AGENT_MAX_TOKENS_PER_RUN", 8_000)


LIMITS = Limits()


class QuotaError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class _State:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.day = date.today()
        self.concurrent = 0
        self.runs_by_user: dict[str, int] = {}
        self.tokens_today = 0

    def _rollover(self) -> None:
        today = date.today()
        if today != self.day:
            self.day = today
            self.runs_by_user.clear()
            self.tokens_today = 0


_STATE = _State()


class Reservation:
    """Acquired budget for one run. Use as a context manager; call
    `record_usage(total_tokens)` once the provider reports actual usage."""

    def __init__(self, user_id: str, est_tokens: int):
        self.user_id = user_id
        self.est_tokens = est_tokens
        self.actual_tokens = 0
        self._active = False

    def record_usage(self, total_tokens: int) -> None:
        self.actual_tokens = max(0, int(total_tokens or 0))

    def __enter__(self) -> "Reservation":
        with _STATE.lock:
            _STATE._rollover()
            if self.est_tokens > LIMITS.max_tokens_per_run:
                raise QuotaError("token_budget_exceeds_per_run_cap")
            if _STATE.concurrent >= LIMITS.max_concurrent:
                raise QuotaError("max_concurrent_runs")
            if _STATE.runs_by_user.get(self.user_id, 0) >= LIMITS.per_user_per_day:
                raise QuotaError("per_user_daily_run_cap")
            # reserve at the estimate; over-budget projected spend is refused.
            if _STATE.tokens_today + self.est_tokens > LIMITS.global_tokens_per_day:
                raise QuotaError("global_daily_token_cap")
            _STATE.concurrent += 1
            _STATE.runs_by_user[self.user_id] = _STATE.runs_by_user.get(self.user_id, 0) + 1
            _STATE.tokens_today += self.est_tokens
            self._active = True
        return self

    def __exit__(self, *exc) -> None:
        with _STATE.lock:
            if not self._active:
                return
            _STATE.concurrent = max(0, _STATE.concurrent - 1)
            # reconcile: replace the estimate with actual usage.
            _STATE.tokens_today += (self.actual_tokens - self.est_tokens)
            if _STATE.tokens_today < 0:
                _STATE.tokens_today = 0
            self._active = False


def reserve(user_id: str, est_tokens: int) -> Reservation:
    return Reservation(user_id, est_tokens)


def snapshot() -> dict:
    with _STATE.lock:
        return {
            "day": _STATE.day.isoformat(),
            "concurrent": _STATE.concurrent,
            "tokens_today": _STATE.tokens_today,
            "runs_by_user": dict(_STATE.runs_by_user),
        }


def demo() -> None:
    os.environ["AGENT_MAX_CONCURRENT_RUNS"] = "1"
    os.environ["AGENT_MAX_TOKENS_PER_RUN"] = "1000"
    r = reserve("u1", 500)
    with r:
        assert snapshot()["concurrent"] == 1
        # concurrency cap: a second run while one is active is refused
        try:
            with reserve("u2", 100):
                assert False, "should have hit concurrency cap"
        except QuotaError as e:
            assert e.reason == "max_concurrent_runs"
        r.record_usage(120)
    assert snapshot()["concurrent"] == 0
    assert snapshot()["tokens_today"] == 120, snapshot()  # reconciled to actual

    # per-run token cap
    try:
        with reserve("u1", 99_999):
            assert False
    except QuotaError as e:
        assert e.reason == "token_budget_exceeds_per_run_cap"
    for k in ("AGENT_MAX_CONCURRENT_RUNS", "AGENT_MAX_TOKENS_PER_RUN"):
        os.environ.pop(k, None)
    print("OK: quota (concurrency, per-run cap, token reconciliation)")


if __name__ == "__main__":
    demo()
