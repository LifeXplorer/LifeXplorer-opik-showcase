from types import SimpleNamespace

import litellm

from review_router import router
from review_router.diffs import Diff


def fake_completion(**kwargs):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="SUMMARY: ok"))],
        usage=SimpleNamespace(total_tokens=42),
        _hidden_params={"response_cost": 0.0005},
    )


def test_review_diff_runs_with_tracking_disabled(monkeypatch):
    # review_diff is wrapped in @opik.track; with OPIK_TRACK_DISABLE=true the decorator is a pass-through.
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")
    monkeypatch.setattr(litellm, "completion", fake_completion)
    review = router.review_diff("openai/gpt-4o-mini", Diff("d", "+x"), "run1")
    assert (review.model, review.tokens, review.cost_usd) == ("openai/gpt-4o-mini", 42, 0.0005)
    assert review.summary == "SUMMARY: ok"


def test_run_all_sends_every_diff_to_every_model(monkeypatch):
    monkeypatch.setattr(litellm, "completion", fake_completion)
    diffs = [Diff("a", "+1"), Diff("b", "+2")]
    reviews = router.run_all(["m1", "m2"], diffs, "run1")
    assert [(r.model, r.diff) for r in reviews] == [("m1", "a"), ("m1", "b"), ("m2", "a"), ("m2", "b")]
