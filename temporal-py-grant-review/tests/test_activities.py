import dataclasses
import json
from types import SimpleNamespace

import pytest
from temporalio.testing import ActivityEnvironment

import activities
from models import Application, BudgetCheck, Screening


def screening(**kw) -> Screening:
    return Screening(**{"category": "garden", "requested_amount": 4200, "fit_score": 5, "summary": "x", **kw})


def test_parse_screening_clamps_score_and_normalises_category():
    s = activities.parse_screening(json.dumps({"category": "Sports", "requested_amount": "900", "fit_score": 9, "summary": "s"}))
    assert (s.category, s.requested_amount, s.fit_score) == ("other", 900, 5)


def test_decide_needs_fit_and_budget():
    ok = BudgetCheck("garden", 4200, 5000, True)
    broke = BudgetCheck("youth", 9800, 6000, False)
    assert activities.decide(screening(), ok) == "approved"
    assert activities.decide(screening(fit_score=2), ok) == "declined"
    assert activities.decide(screening(), broke) == "declined"


async def test_check_budget_fails_first_attempt_then_succeeds():
    env = ActivityEnvironment()
    with pytest.raises(RuntimeError, match="Ledger service unavailable"):
        await env.run(activities.check_budget, screening())  # default attempt is 1
    env.info = dataclasses.replace(env.info, attempt=2)
    result = await env.run(activities.check_budget, screening())
    assert result.affordable and result.remaining_before == 5000


class FakeOpenAI:
    """Stands in for AsyncOpenAI: no network, no key."""

    def __init__(self):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    async def create(self, **kwargs):
        message = SimpleNamespace(content='{"category": "garden", "requested_amount": 4200, "fit_score": 4, "summary": "ok"}')
        return SimpleNamespace(
            choices=[SimpleNamespace(message=message)],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
            model="gpt-4o-mini-test",
        )


async def test_traced_activity_runs_without_a_tracing_setup(monkeypatch):
    # The LLM span is a plain OpenTelemetry span: with no exporter configured (as in unit tests)
    # it is a no-op, and the activity behaves exactly the same.
    monkeypatch.setattr(activities, "AsyncOpenAI", FakeOpenAI)
    app = Application("GR-0", "Test Group", "t@example.com", "A garden for $4,200.")
    result = await ActivityEnvironment().run(activities.screen_application, app)
    assert (result.category, result.fit_score) == ("garden", 4)
