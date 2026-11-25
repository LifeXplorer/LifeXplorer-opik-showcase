"""Ground truth for the race-results questions, computed without pandas or any model.

The agent answers by generating pandas code; these functions answer the same
questions with plain stdlib code so a run can be graded.
"""

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

CSV_PATH = Path(__file__).parent / "data" / "saltmarsh_2025.csv"


def parse_time(value: str) -> int:
    """'H:MM:SS' -> seconds."""
    h, m, s = (int(p) for p in value.split(":"))
    return h * 3600 + m * 60 + s


def format_time(seconds: int) -> str:
    return f"{seconds // 3600}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def load_rows(path: Path = CSV_PATH) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def women_40_44_winner(rows: list[dict[str, str]]) -> tuple[str, str]:
    finishers = [r for r in rows if r["status"] == "FIN" and r["gender"] == "F" and r["age_group"] == "40-44"]
    best = min(finishers, key=lambda r: parse_time(r["chip_time"]))
    return best["runner"], best["chip_time"]


def negative_split_share(rows: list[dict[str, str]], min_finishers: int = 5) -> tuple[str, float]:
    """Club with the highest % of finishers whose second half beat their first half."""
    totals: dict[str, list[int]] = {}
    for r in rows:
        if r["status"] != "FIN":
            continue
        half, full = parse_time(r["half_split"]), parse_time(r["chip_time"])
        t = totals.setdefault(r["club"], [0, 0])
        t[1] += 1
        t[0] += (full - half) < half
    shares = {c: 100 * neg / n for c, (neg, n) in totals.items() if n >= min_finishers}
    club = max(shares, key=shares.get)
    return club, round(shares[club], 1)


def highest_dnf_rate(rows: list[dict[str, str]]) -> tuple[str, float]:
    """Age group with the highest share of starters who did not finish."""
    totals: dict[str, list[int]] = {}
    for r in rows:
        t = totals.setdefault(r["age_group"], [0, 0])
        t[1] += 1
        t[0] += r["status"] == "DNF"
    rates = {g: 100 * dnf / n for g, (dnf, n) in totals.items()}
    group = max(rates, key=rates.get)
    return group, round(rates[group], 1)


@dataclass
class Expected:
    """What a correct answer must contain: entity substrings and numbers (value, tolerance)."""

    entities: list[str]
    numbers: list[tuple[float, float]] = field(default_factory=list)


def expected_answers(rows: list[dict[str, str]]) -> list[Expected]:
    name, time = women_40_44_winner(rows)
    club, share = negative_split_share(rows)
    group, rate = highest_dnf_rate(rows)
    return [
        Expected(entities=[name, time]),
        Expected(entities=[club], numbers=[(share, 1.0)]),
        Expected(entities=[group], numbers=[(rate, 1.0)]),
    ]


def check_answer(answer: str, expected: Expected) -> list[str]:
    """Return the problems with an answer; an empty list means it is correct."""
    text = str(answer)
    problems = [f"missing {e!r}" for e in expected.entities if e.lower() not in text.lower()]
    found = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)]
    for value, tol in expected.numbers:
        if not any(abs(f - value) <= tol for f in found):
            problems.append(f"no number within {tol} of {value}")
    return problems
