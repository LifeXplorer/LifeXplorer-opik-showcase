import json

import claims_core
import main


def test_payout_subtracts_deductible():
    out = claims_core.estimate_payout("POL-1001", 1800)
    assert out["estimated_payout_usd"] == 1300


def test_payout_is_capped_at_limit():
    out = claims_core.estimate_payout("POL-1001", 50000)
    assert out["estimated_payout_usd"] == 20000


def test_lapsed_policy_cannot_open_claim():
    assert "lapsed" in claims_core.open_claim("POL-3003", "stolen car")["error"]


def test_unknown_policy():
    assert "not found" in claims_core.lookup_policy("POL-0000")["error"]


def test_open_claim_returns_id():
    out = claims_core.open_claim("pol-2002", "burst pipe")
    assert out["status"] == "opened" and out["claim_id"].startswith("CLM-")


def test_run_turn_under_trace_block_with_tracking_disabled(monkeypatch):
    # run_turn opens an SDK trace(group_id=...) block; with the Opik
    # processor inert (OPIK_TRACK_DISABLE) it must not get in the way.
    class FakeResult:
        last_agent = main.auto_agent
        final_output = "ok"

        def to_input_list(self):
            return [{"role": "assistant", "content": "ok"}]

    monkeypatch.setattr(main.Runner, "run_sync", lambda agent, history: FakeResult())
    result = main.run_turn([{"role": "user", "content": "hi"}], "t-1")
    assert result.last_agent.name == "Auto Claims Agent"


def test_routing_rows_flag_misroutes():
    rows = [{"conversation": "a", "expected": "X", "routed_to": "X"},
            {"conversation": "b", "expected": "X", "routed_to": "Y"}]
    assert [r["ok"] for r in main.score_routing(rows)] == [True, False]


def test_verify_flags_specialist_without_tool_calls():
    import verify

    talking = verify.summarize_trace([("general", "Task"), ("general", "Handoff"),
                                      ("general", "Auto Claims Agent")])
    working = verify.summarize_trace([("general", "Handoff"),
                                      ("general", "Auto Claims Agent"),
                                      ("tool", "lookup_policy")])
    assert verify.check_thread([working], "Auto Claims Agent") == []
    assert verify.check_thread([talking], "Auto Claims Agent") == [
        "turn 1: specialist made no tool calls"]
