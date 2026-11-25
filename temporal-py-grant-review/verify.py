"""Check what the demo left in Opik: one trace per application, spans from two processes,
and the failed ledger attempt next to its successful retry.

    uv run verify.py
"""
import sys

import opik

from otel import PROJECT_NAME


def main() -> int:
    client = opik.Opik()  # reads the Opik URL / workspace from the environment or ~/.opik.config
    traces = client.search_traces(project_name=PROJECT_NAME, max_results=50)
    problems: list[str] = []
    for trace in sorted(traces, key=lambda t: t.start_time):
        spans = sorted(client.search_spans(project_name=PROJECT_NAME, trace_id=trace.id, max_results=200), key=lambda s: s.start_time)
        attempts = [s for s in spans if s.name == "RunActivity:check_budget"]
        failed = [s for s in attempts if s.error_info]
        llm = [s for s in spans if s.type == "llm"]
        pids = {(s.metadata or {}).get("pid") for s in spans} - {None}
        print(f"{trace.name}: {len(spans)} spans, {len(llm)} llm, {len(attempts)} check_budget attempts "
              f"({len(failed)} failed), pids={sorted(pids)}, cost={trace.total_estimated_cost}, usage={trace.usage}")
        for s in failed:
            print(f"    error on {s.name}: {s.error_info.message}")
        if len(pids) != 2:
            problems.append(f"{trace.name}: expected spans from 2 processes, saw pids {sorted(pids)}")
        if len(attempts) != 2 or len(failed) != 1:
            problems.append(f"{trace.name}: expected one failed and one successful attempt")
        if len(llm) != 2 or not trace.total_estimated_cost:
            problems.append(f"{trace.name}: expected 2 llm spans and a non-zero cost")
    if not traces:
        problems.append("no traces found: run main.py first")
    print("\n".join(["OK"] if not problems else ["PROBLEMS:", *problems]))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
