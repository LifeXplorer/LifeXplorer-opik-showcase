"""Read the run back from Opik and check what the span trees say.

`main.py` only sees which agent answered last (`routed_to`). This script
looks inside each trace: was there a Handoff span, and did the specialist
actually call tools, or just talk?
"""

import os
from collections import defaultdict

os.environ.setdefault("OPIK_PROJECT_NAME", "openai-agents-insurance-claims")
PROJECT = os.environ["OPIK_PROJECT_NAME"]


def summarize_trace(spans: list[tuple[str, str]]) -> dict:
    """spans: (type, name) in start order -> handoff target and tools used."""
    names = [name for _, name in spans]
    handoff_at = names.index("Handoff") if "Handoff" in names else None
    specialist = None
    if handoff_at is not None:
        # The span right after Handoff is the agent that took over.
        specialist = names[handoff_at + 1] if handoff_at + 1 < len(names) else None
    tools = [name for type_, name in spans if type_ == "tool"]
    return {"handed_off": handoff_at is not None, "specialist": specialist,
            "tools": tools}


def check_thread(turns: list[dict], expected: str) -> list[str]:
    """Return problems for one conversation (empty list = healthy)."""
    problems = []
    for i, turn in enumerate(turns, start=1):
        if not turn["handed_off"]:
            problems.append(f"turn {i}: no handoff span")
        elif turn["specialist"] != expected:
            problems.append(f"turn {i}: handed to {turn['specialist']}, expected {expected}")
        if not turn["tools"]:
            problems.append(f"turn {i}: specialist made no tool calls")
    return problems


def main() -> int:
    import opik
    from main import CONVERSATIONS

    client = opik.Opik()
    # Opik objects: search_traces/search_spans read back the traces and
    # spans that OpikTracingProcessor sent during the run.
    traces = sorted(client.search_traces(project_name=PROJECT, max_results=200),
                    key=lambda t: t.start_time)
    threads = defaultdict(list)
    for t in traces:
        spans = sorted(client.search_spans(project_name=PROJECT, trace_id=t.id,
                                           max_results=200),
                       key=lambda s: s.start_time)
        threads[t.thread_id].append(summarize_trace([(s.type, s.name) for s in spans]))

    failed = 0
    print(f"{len(traces)} traces in {len(threads)} threads, project {PROJECT}")
    for thread_id, turns in threads.items():
        name = thread_id.rsplit("-", 1)[0]
        problems = check_thread(turns, CONVERSATIONS[name]["expected"])
        failed += bool(problems)
        tools = [t for turn in turns for t in turn["tools"]]
        print(f"{'FAIL' if problems else 'ok  '} {thread_id}: tools={tools} {problems}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
