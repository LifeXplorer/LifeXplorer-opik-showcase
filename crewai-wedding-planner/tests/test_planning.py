import os

os.environ["OPIK_TRACK_DISABLE"] = "true"  # keep unit tests off the network

from planning import (
    budget_snapshot,
    catering_cost,
    check_plan,
    shuttle_cost,
    shuttle_runs,
    timeline_minutes,
)

GOOD = "\n".join(f"{h:02d}:00 - step" for h in range(11, 19)) + "\n22:30 - music curfew\n23:15 - last shuttle"


def test_catering_cost():
    assert catering_cost(84, 6) == 84 * 68 + 6 * 32


def test_shuttle_runs_and_minimum_hours():
    assert shuttle_runs(40) == 2
    assert shuttle_cost(40) == 190  # 2 runs = 0.8h, billed at the 2h minimum
    assert shuttle_cost(200) == round(9 * 24 / 60 * 95)


def test_budget_snapshot_mentions_total_and_headroom():
    text = budget_snapshot(84, 6, 40)
    assert "Projected total: 27294 USD" in text
    assert "headroom 10706 USD" in text


def test_timeline_minutes_ignores_bullets_and_prose():
    assert timeline_minutes("- 09:30 - a\n**10:05** - b\nnoon - c") == [570, 605]


def test_check_plan_passes_good_plan():
    assert check_plan(GOOD) == []


def test_check_plan_flags_order_curfew_and_late_entry():
    problems = check_plan("12:00 - a\n11:00 - b\n23:45 - c")
    assert any("chronological" in p for p in problems)
    assert any("22:30" in p for p in problems)
    assert any("last shuttle" in p for p in problems)


def test_traced_crew_module_imports_with_tracking_disabled(monkeypatch):
    # Importing main builds the crew and calls track_crewai; with tracking disabled it must not need Opik or a key.
    monkeypatch.setenv("OPENAI_API_KEY", "test-not-real")
    import main

    assert main.PROJECT == "crewai-wedding-planner"
    assert len(main.crew.tasks) == 3
