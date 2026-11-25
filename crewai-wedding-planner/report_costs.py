"""Print tokens and dollar cost per agent for the newest trace in the project."""

import opik

from main import PROJECT

client = opik.Opik()
trace = client.search_traces(project_name=PROJECT, max_results=1)[0]
spans = client.search_spans(project_name=PROJECT, trace_id=trace.id, max_results=500)
by_id = {s.id: s for s in spans}


def agent_of(span):
    """track_crewai nests spans as kickoff -> 'Task: ...' -> '<agent role>' -> ... -> llm."""
    while span.parent_span_id in by_id:
        parent = by_id[span.parent_span_id]
        if parent.name.startswith("Task: "):
            return span.name
        span = parent
    return "unknown"


# usage and total_estimated_cost live on the llm spans; roll them up to the agent above them.
totals: dict[str, dict] = {}
for s in spans:
    if s.type == "llm":
        t = totals.setdefault(agent_of(s), {"calls": 0, "tokens": 0, "cost": 0.0})
        t["calls"] += 1
        t["tokens"] += (s.usage or {}).get("total_tokens", 0)
        t["cost"] += s.total_estimated_cost or 0.0

print(f"trace {trace.id}: {len(spans)} spans")
for name, t in totals.items():
    print(f"{name:24s} llm_calls={t['calls']} tokens={t['tokens']} cost=${t['cost']:.5f}")
print(f"{'TOTAL':24s} tokens={sum(t['tokens'] for t in totals.values())} cost=${sum(t['cost'] for t in totals.values()):.5f}")
