"""Route each diff to each model through LiteLLM and record cost, latency and tokens."""

import time
from dataclasses import dataclass

import litellm

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


def review_diff(model: str, diff: Diff) -> Review:
    """One model, one diff. LiteLLM gives every provider the same completion() call."""
    start = time.perf_counter()
    response = litellm.completion(
        model=model,
        messages=build_messages(diff.text),
        temperature=0,
        max_tokens=400,
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


def run_all(models: list[str], diffs: list[Diff]) -> list[Review]:
    """Every diff goes to every model, one model after the other."""
    reviews = []
    for model in models:
        for diff in diffs:
            reviews.append(review_diff(model, diff))
    return reviews
