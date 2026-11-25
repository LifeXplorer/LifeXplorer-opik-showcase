"""Run the real CodeAgent against a stub model, with tracing off: no keys, no Opik."""

from smolagents import CodeAgent, Model
from smolagents.models import ChatMessage

import main
from analysis import check_answer, expected_answers, load_rows
from feedback import SCORE_NAME, build_scores, find_trace_ids
from tracing import setup_tracing


class StubModel(Model):
    """Replies with fixed pandas code, the way the real model would."""

    def generate(self, messages, **kwargs):
        code = (
            "import pandas as pd\n"
            f"df = pd.read_csv({str(main.CSV_PATH)!r})\n"
            "dnf = df.assign(d=df.status == 'DNF').groupby('age_group').d.mean().mul(100)\n"
            "final_answer(f'{dnf.idxmax()} has the highest DNF rate: {dnf.max():.1f}%')\n"
        )
        return ChatMessage(role="assistant", content=f"Thought: compute it.\n<code>\n{code}</code>")


def test_tracing_switch_off_returns_no_provider(monkeypatch):
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")
    assert setup_tracing("any-project") is None


def test_agent_runs_generated_pandas_code_with_tracing_disabled(monkeypatch):
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")
    agent = CodeAgent(tools=[], model=StubModel(), additional_authorized_imports=["pandas"], max_steps=3)
    answer = main.ask(agent, main.QUESTIONS[2])
    assert check_answer(answer, expected_answers(load_rows())[2]) == []


class FakeTrace:
    def __init__(self, id, input, start_time):
        self.id, self.input, self.start_time = id, input, start_time


def test_scores_land_on_the_newest_matching_trace():
    q1, q2 = main.QUESTIONS[0], main.QUESTIONS[1]
    traces = [
        FakeTrace("old", {"value": {"task": f"brief {q1}"}}, 1),
        FakeTrace("new", {"value": {"task": f"brief {q1}"}}, 2),
        FakeTrace("two", {"value": {"task": f"brief {q2}"}}, 1),
    ]
    ids = find_trace_ids(traces, [q1, q2])
    assert ids == {q1: "new", q2: "two"}
    scores = build_scores(ids, {q1: [], q2: ["missing 'Dune Pacers'"]})
    assert [(s["id"], s["name"], s["value"]) for s in scores] == [("new", SCORE_NAME, 1.0), ("two", SCORE_NAME, 0.0)]
    assert "Dune Pacers" in scores[1]["reason"]
