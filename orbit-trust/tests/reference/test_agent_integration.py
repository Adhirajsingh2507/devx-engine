"""N3 ADK↔Groq integration — T34–T37 (doc 09).

Every case is labeled LIVE_GROQ or DETERMINISTIC_FALLBACK. The host-validation
and fallback cases (T35–T37) run deterministically and offline — no key needed.
The happy-path cases (T34, T36) run live when GROQ_ENABLED + GROQ_API_KEY are
present (the spike loads them from .env) and otherwise exercise the labeled
deterministic fallback. `__main__` writes n3_test_results.json and, if a live
run succeeds, one genuine captured trace (never fabricated).

  T34  live/fallback investigate yields a host-validated, host-owned packet
  T35  host rejects invented / omitted / mis-templated / extra-field selections
  T36  prompt injection in finding text is data — flagged, masked, urgency unchanged
  T37  disabled key / timeout / 429 / malformed each -> labeled deterministic fallback
"""

from __future__ import annotations

import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orbit_trust import agent, assessment, investigator, sanitize  # noqa: E402
from orbit_trust.models import parse_utc  # noqa: E402

FX = ROOT / "data" / "fixtures" / "encounter_reference.json"
NOW = parse_utc("2026-09-11T12:20:00Z")  # fixed demo clock (doc 02)
RESULTS: list[dict] = []


def _report(case_id: str) -> dict:
    for c in json.loads(FX.read_text())["cases"]:
        if c["id"] == case_id:
            return copy.deepcopy(c["input"])
    raise AssertionError(case_id)


def _assessment(case_id: str) -> dict:
    a = assessment.assess(_report(case_id), now=NOW).to_dict()
    a["assessment_id"] = f"asmt-{case_id}"
    return a


def _record(test: str, mode: str, ok: bool, detail: str = "") -> None:
    RESULTS.append({"test": test, "mode": mode, "status": "PASS" if ok else "FAIL", "detail": detail})
    assert ok, f"{test} [{mode}] FAILED: {detail}"


def _live() -> bool:
    import os
    if os.environ.get("N3_OFFLINE") == "1":   # force the fallback/validation path
        return False
    investigator._load_env_file()
    return investigator.is_enabled()


# --- T34: happy path, dual-mode -------------------------------------------

def test_t34_investigate_host_owned():
    a = _assessment("sigma-200")  # risk-exceeded case
    packet = agent.investigate(a)
    mode = "LIVE_GROQ" if packet["generation_mode"] == "groq" else "DETERMINISTIC_FALLBACK"
    sel = packet["selection"]

    # host owns the outcome in BOTH modes
    ok = (
        agent.validate_selection(sel, a) is None
        and sel["summary_template_code"] == agent._summary_code(a)          # host-supported summary
        and packet["authoritative_text"] == agent._SUMMARY_TEXT[sel["summary_template_code"]]
        and "RISK_THRESHOLD_EXCEEDED" in sel["ordered_finding_ids"]          # required finding present
    )
    if mode == "LIVE_GROQ":
        ok = ok and "trace" in packet and packet["trace"]["tool_calls"] and packet["trace"]["total_tokens"] > 0
    _record("T34_investigate_host_owned", mode, ok,
            f"summary={sel['summary_template_code']} reason={packet.get('fallback_reason','-')}")


# --- T35: host rejects model over-reach (deterministic, offline) ----------

def test_t35_host_rejects_overreach():
    a = _assessment("sigma-200")
    good = agent._select(a)  # a valid selection to mutate

    def rejects(mutate, expected_prefix):
        sel = copy.deepcopy(good)
        mutate(sel)
        try:
            investigator._validate(sel, a)
            return False
        except investigator.LiveUnavailable as e:
            return e.reason.startswith(expected_prefix)

    cases = {
        "invented_finding": (lambda s: s["ordered_finding_ids"].append("finding-does-not-exist"),
                             "invalid:cited_unknown_finding"),
        "omitted_required": (lambda s: s.__setitem__("ordered_finding_ids", []),
                             "invalid:required_finding_omitted"),
        "wrong_template":   (lambda s: s.__setitem__("summary_template_code", "MONITOR_SUPPORTED"),
                             "invalid:summary_template_not_supported_by_facts"),
        "schema_extra":     (lambda s: s.__setitem__("unvalidated_summary", "safe"),
                             "malformed:schema"),
    }
    for name, (mut, exp) in cases.items():
        _record(f"T35_{name}", "DETERMINISTIC_FALLBACK", rejects(mut, exp), exp)

    # forbidden tool: only the three read-only tools are allowlisted
    forbidden = "send_satellite_command" not in investigator.ALLOWLISTED_TOOLS \
        and "fetch_url" not in investigator.ALLOWLISTED_TOOLS \
        and len(investigator.ALLOWLISTED_TOOLS) == 3
    _record("T35_forbidden_tool_denied", "DETERMINISTIC_FALLBACK", forbidden,
            f"allowlist={investigator.ALLOWLISTED_TOOLS}")


# --- T36: injection in finding text is data -------------------------------

def test_t36_injection_is_data():
    inj = json.loads((ROOT / "data" / "fixtures" / "adversarial_cases.json").read_text())
    payload = next(c["untrusted_text"] for c in inj["cases"] if c["id"] == "imported-injection")

    a = _assessment("sigma-200")
    clean_summary = agent._summary_code(a)

    poisoned = copy.deepcopy(a)
    poisoned["findings"][0]["detail"] = payload  # inject into an existing finding's text

    # sanitize raises the audit flag; there is no fetch/network tool in the
    # allowlist, so the override *cannot* trigger an external call structurally.
    s = sanitize.sanitize_text(payload)
    no_exfil_tool = not any(t in investigator.ALLOWLISTED_TOOLS for t in ("fetch_url", "send_satellite_command"))

    packet = agent.investigate(poisoned)
    mode = "LIVE_GROQ" if packet["generation_mode"] == "groq" else "DETERMINISTIC_FALLBACK"
    # the definitive guard: host-owned summary/urgency is unchanged by the injected text
    unchanged = packet["selection"]["summary_template_code"] == clean_summary \
        and agent.validate_selection(packet["selection"], poisoned) is None
    _record("T36_injection_is_data", mode, s.injection_detected and no_exfil_tool and unchanged,
            f"injection_flagged={s.injection_detected} summary={packet['selection']['summary_template_code']}")


# --- T37: failure modes -> labeled deterministic fallback -----------------

def test_t37_failure_modes_fallback():
    a = _assessment("sigma-200")
    orig_run, orig_enabled = investigator.run_investigation, investigator.is_enabled
    try:
        # force the live branch, then inject each failure and confirm labeled fallback
        investigator.is_enabled = lambda: True
        for reason in ("timeout", "rate_limited", "malformed:bad_json", "quota:global_daily_token_cap"):
            investigator.run_investigation = lambda _a, reason=reason, **k: (_ for _ in ()).throw(
                investigator.LiveUnavailable(reason))
            packet = agent.investigate(a)
            ok = packet["generation_mode"] == "template_fallback" and packet.get("fallback_reason") == reason \
                and agent.validate_selection(packet["selection"], a) is None
            _record(f"T37_fallback_{reason.split(':')[0]}", "DETERMINISTIC_FALLBACK", ok, reason)
    finally:
        investigator.run_investigation, investigator.is_enabled = orig_run, orig_enabled

    # the disabled-key path (no monkeypatch) also yields a labeled fallback
    orig_enabled2 = investigator.is_enabled
    try:
        investigator.is_enabled = lambda: False
        packet = agent.investigate(a)
        _record("T37_fallback_disabled", "DETERMINISTIC_FALLBACK",
                packet["generation_mode"] == "template_fallback"
                and packet.get("fallback_reason") == "groq_disabled_or_no_key", "groq_disabled_or_no_key")
    finally:
        investigator.is_enabled = orig_enabled2


def _capture_live_trace() -> dict | None:
    """Requirement 10: one genuine successful live run, or honest None."""
    if not _live():
        return None
    a = _assessment("sigma-200")
    packet = agent.investigate(a)
    if packet["generation_mode"] != "groq":
        return {"live_attempted": True, "fallback_reason": packet.get("fallback_reason")}
    return {
        "live_attempted": True,
        "generation_mode": "groq",
        "summary_template_code": packet["selection"]["summary_template_code"],
        "authoritative_text": packet["authoritative_text"],
        "selection": packet["selection"],
        "retries": packet.get("retries", 0),
        "trace": packet["trace"],
    }


def _run_all() -> int:
    live = _live()
    banner = "LIVE_GROQ (key present)" if live else "DETERMINISTIC_FALLBACK (no key)"
    print(f"== N3 T34–T37 :: mode={banner} ==")
    for fn in (test_t34_investigate_host_owned, test_t35_host_rejects_overreach,
               test_t36_injection_is_data, test_t37_failure_modes_fallback):
        fn()
    trace = _capture_live_trace()
    out = {"live_enabled": live, "results": RESULTS, "live_trace": trace}
    (ROOT / "n3_test_results.json").write_text(json.dumps(out, indent=2, default=str))
    npass = sum(r["status"] == "PASS" for r in RESULTS)
    for r in RESULTS:
        print(f"  [{r['status']}] {r['test']:34s} {r['mode']:22s} {r['detail']}")
    print(f"== {npass}/{len(RESULTS)} PASS ; live_trace_captured={bool(trace and trace.get('generation_mode')=='groq')} ==")
    print("results -> n3_test_results.json")
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(_run_all())
