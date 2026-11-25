"""Read the per-model numbers back out of Opik, so the comparison table comes from what Opik recorded."""

import opik

from review_router.config import PROJECT_NAME


def fetch_samples(run_id: str, project: str = PROJECT_NAME) -> list[tuple[str, float, float, int]]:
    """Return (model, latency_s, cost_usd, tokens) for every llm span tagged with this run."""
    client = opik.Opik(project_name=project)
    # Every review span carries a run:<id> tag (set in router.py), so one filter selects one CLI run.
    spans = client.search_spans(
        project_name=project,
        filter_string=f'type = "llm" and tags contains "run:{run_id}"',
        truncate=True,
    )
    samples = []
    for span in spans:
        latency = (span.end_time - span.start_time).total_seconds()
        # total_estimated_cost is the cost stored on the span (LiteLLM sends its own price, so both tables agree).
        samples.append((span.model or "unknown", latency, span.total_estimated_cost or 0.0, (span.usage or {}).get("total_tokens", 0)))
    return samples
