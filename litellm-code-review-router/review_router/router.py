"""Route each diff to each model through LiteLLM and record cost, latency and tokens."""

import time
from dataclasses import dataclass

import litellm
import opik
from opik import opik_context

from review_router.config import PROJECT_NAME
from review_router.diffs import Diff
from review_router.prompts import build_messages


@dataclass(frozen=True)
class Review:
    model: str
    diff: str
    summary: str
    latency_s: float
    cost_usd: float
    tokens: int


# @track opens one trace per (model, diff) review; the LiteLLM span nests inside it, so the
# trace row in Opik shows the review's total duration and cost next to its model tag.
@opik.track(name="review_diff", project_name=PROJECT_NAME)
def review_diff(model: str, diff: Diff, run_id: str = "") -> Review:
    """One model, one diff. LiteLLM gives every provider the same completion() call."""
    tags = [f"model:{model.split('/')[-1]}", f"diff:{diff.name}", f"run:{run_id}"]
    # Tags on the trace make it filterable by model and by CLI run in the traces table.
    opik_context.update_current_trace(tags=tags)
    start = time.perf_counter()
    response = litellm.completion(
        model=model,
        messages=build_messages(diff.text),
        temperature=0,
        max_tokens=400,
        # Inside @track, LiteLLM must be told the current span, or its llm span is logged as a
        # separate orphan trace instead of nesting under review_diff. Tags land on the span too.
        metadata={"opik": {"current_span_data": opik_context.get_current_span_data(), "tags": tags}},
    )
    latency = time.perf_counter() - start
    return Review(
        model=model,
        diff=diff.name,
        summary=response.choices[0].message.content or "",
        latency_s=latency,
        # LiteLLM prices each response from its own model table.
        cost_usd=response._hidden_params.get("response_cost") or 0.0,
        tokens=response.usage.total_tokens,
    )


def run_all(models: list[str], diffs: list[Diff], run_id: str = "") -> list[Review]:
    """Every diff goes to every model, one model after the other."""
    reviews = []
    for model in models:
        for diff in diffs:
            reviews.append(review_diff(model, diff, run_id))
    return reviews
