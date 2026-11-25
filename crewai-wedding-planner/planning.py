"""Plain-Python helpers: no LLM, no Opik, so they unit-test offline."""

import math
import re

ADULT_PLATE = 68
CHILD_PLATE = 32
SHUTTLE_SEATS = 24
SHUTTLE_RATE_PER_HOUR = 95
SHUTTLE_MIN_HOURS = 2
SHUTTLE_ROUND_TRIP_MIN = 24  # 12 minutes each way


def catering_cost(adults: int, children: int) -> int:
    return adults * ADULT_PLATE + children * CHILD_PLATE


def shuttle_runs(guests_riding: int) -> int:
    return math.ceil(guests_riding / SHUTTLE_SEATS)


def shuttle_cost(guests_riding: int) -> int:
    """Hours needed for all runs, billed at the 2-hour minimum."""
    hours = shuttle_runs(guests_riding) * SHUTTLE_ROUND_TRIP_MIN / 60
    return round(max(hours, SHUTTLE_MIN_HOURS) * SHUTTLE_RATE_PER_HOUR)


def budget_snapshot(adults: int, children: int, riding: int) -> str:
    """Fixed numbers handed to the agents so they don't do arithmetic themselves."""
    fixed = {"Florist": 3400, "Band": 5200, "Photographer": 3100}
    catering = catering_cost(adults, children)
    shuttle = shuttle_cost(riding)
    spent = 9500
    total = spent + catering + shuttle + sum(fixed.values())
    lines = [f"Venue deposit (paid): {spent} USD", f"Catering ({adults} adults, {children} children): {catering} USD"]
    lines += [f"{name}: {cost} USD" for name, cost in fixed.items()]
    lines.append(f"Shuttle ({shuttle_runs(riding)} runs for {riding} riders): {shuttle} USD")
    lines.append(f"Projected total: {total} USD of 38000 USD budget (headroom {38000 - total} USD)")
    return "\n".join(lines)


_TIME = re.compile(r"^\W*(\d{1,2}):(\d{2})\b", re.MULTILINE)


def timeline_minutes(plan: str) -> list[int]:
    """Minutes-after-midnight for every line that starts with HH:MM."""
    return [int(h) * 60 + int(m) for h, m in _TIME.findall(plan)]


def check_plan(plan: str) -> list[str]:
    """Cheap guardrails on the finished plan; returns human-readable problems."""
    problems = []
    times = timeline_minutes(plan)
    if len(times) < 8:
        problems.append(f"only {len(times)} timed entries (expected at least 8)")
    if times != sorted(times):
        problems.append("timeline is not in chronological order")
    if times and max(times) > 23 * 60 + 15:
        problems.append("an entry is scheduled after the last shuttle (23:15)")
    if "22:30" not in plan:
        problems.append("music curfew (22:30) is not mentioned")
    return problems
