"""Offline tests: no provider keys, no Opik. Run with
env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest"""
import asyncio
import json

import tracing
import triage
from tools import lookup_safe_range, lookup_tank, safe_range, tank_profile

ANSWER = """Severity: Urgent
Why: 0.25 ppm is above the 0.1 ppm urgent line.
Action: Do a 20% water change now.
Notify: Marisol Quint"""


def test_parse_triage_reads_all_fields_and_normalises_severity():
    out = triage.parse_triage(ANSWER)
    assert out["severity"] == "urgent"
    assert out["notify"] == "Marisol Quint"
    assert out["action"].startswith("Do a 20%")


def test_parse_triage_flags_missing_or_invalid_severity():
    out = triage.parse_triage("Severity: panic\nAction: run")
    assert out["severity"] is None and out["why"] is None and out["action"] == "run"


def test_tank_profile_known_and_unknown():
    assert tank_profile("REEF-01")["type"] == "reef"
    assert "reef-01" in tank_profile("nope")["valid_ids"]


def test_safe_range_thresholds_and_errors():
    assert safe_range("reef", "ammonia_ppm")["urgent_above"] == 0.1
    assert "valid_types" in safe_range("pond", "ph")
    assert "valid_parameters" in safe_range("shrimp", "salinity_ppt")


def test_tool_wrappers_return_json_strings():
    # The @tool objects are what the agent calls; their run() output is the text the model reads.
    assert callable(lookup_tank.run) and callable(lookup_safe_range.run)
    assert json.loads(json.dumps(tank_profile("comm-07")))["keeper"] == "Priya Anand"


def test_build_prompt_mentions_alert_details():
    p = triage.build_prompt({"tank_id": "reef-01", "parameter": "ph", "reading": 7.9, "note": "n"})
    assert "reef-01" in p and "ph = 7.9" in p and "lookup_safe_range" in p


def test_setup_tracing_is_a_noop_when_tracking_disabled(monkeypatch):
    # With OPIK_TRACK_DISABLE=true no exporter or instrumentation is installed, so the app runs offline.
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")
    shutdown = tracing.setup_tracing("x")
    assert shutdown() is None


def test_triage_alert_runs_untraced_with_a_stub_model(monkeypatch):
    class FakeResult:
        class last_message:
            text = ANSWER

    class FakeAgent:
        async def run(self, prompt, **kwargs):
            return FakeResult()

    monkeypatch.setattr(triage, "make_agent", lambda llm=None: FakeAgent())
    out = asyncio.run(triage.triage_alert({"tank_id": "reef-01", "parameter": "ammonia_ppm", "reading": 0.25, "note": ""}))
    assert out["severity"] == "urgent"


def test_opik_attributes_adds_provider_and_tool_keys():
    llm = tracing.opik_attributes({"openinference.span.kind": "LLM", "llm.provider": "openai"})
    assert llm["gen_ai.provider.name"] == "openai"
    tool = tracing.opik_attributes({"openinference.span.kind": "TOOL", "input.value": "{}", "output.value": "x"})
    assert "gen_ai.tool.call.arguments" in tool and "input.value" not in tool
