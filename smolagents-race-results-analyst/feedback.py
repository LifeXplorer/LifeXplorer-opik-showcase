"""Attach the ground-truth verdict to each question's Opik trace as a feedback score."""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import opik

SCORE_NAME = "matches_ground_truth"


def find_trace_ids(traces: Sequence[Any], questions: Sequence[str]) -> dict[str, str]:
    """Map each question to the newest trace whose root input (the task) contains it."""
    found: dict[str, Any] = {}
    for t in traces:
        text = str(t.input)
        for q in questions:
            if q in text and (q not in found or t.start_time > found[q].start_time):
                found[q] = t
    return {q: t.id for q, t in found.items()}


def build_scores(trace_ids: dict[str, str], verdicts: dict[str, list[str]]) -> list[dict[str, Any]]:
    """One feedback score per graded trace: 1.0 when the answer matched, else 0.0 with the reason."""
    return [
        {
            "id": trace_ids[q],
            "name": SCORE_NAME,
            "value": 0.0 if problems else 1.0,
            "reason": "; ".join(problems) or "answer matches the stdlib ground truth",
        }
        for q, problems in verdicts.items()
        if q in trace_ids
    ]


def attach_scores(project: str, started: datetime, verdicts: dict[str, list[str]]) -> int:
    """Score this run's traces in Opik; returns how many traces were scored."""
    client = opik.Opik(project_name=project)
    # OTLP ingestion is asynchronous, so wait until every question's trace is visible.
    # Use a trailing "Z": a "+00:00" offset loses its "+" in transit and Opik rejects the filter.
    since = started.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    traces = client.search_traces(
        project_name=project,
        filter_string=f'start_time >= "{since}"',
        wait_for_at_least=len(verdicts),
        wait_for_timeout=60,
    )
    scores = build_scores(find_trace_ids(traces, list(verdicts)), verdicts)
    # Feedback scores show up as a column in the project's traces table, so you can sort
    # and filter the trace list by "did the number actually match?".
    client.log_traces_feedback_scores(scores, project_name=project)
    client.flush()
    return len(scores)
