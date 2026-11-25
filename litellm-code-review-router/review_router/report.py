"""Per-model comparison table: one row per model, built from plain numbers."""

import statistics
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelRow:
    model: str
    calls: int
    tokens: int
    cost_usd: float
    mean_latency_s: float


def summarize(samples: list[tuple[str, float, float, int]]) -> list[ModelRow]:
    """samples: (model, latency_s, cost_usd, tokens) per call -> one ModelRow per model."""
    grouped: dict[str, list[tuple[float, float, int]]] = defaultdict(list)
    for model, latency, cost, tokens in samples:
        grouped[model].append((latency, cost, tokens))
    rows = []
    for model, calls in grouped.items():
        latencies, costs, tokens = zip(*calls)
        rows.append(ModelRow(model, len(calls), sum(tokens), sum(costs), statistics.mean(latencies)))
    return sorted(rows, key=lambda r: r.cost_usd)


def render_table(rows: list[ModelRow]) -> str:
    lines = [f"{'model':<38} {'calls':>5} {'tokens':>7} {'cost':>11} {'$/call':>10} {'mean latency':>13}"]
    lines.append("-" * len(lines[0]))
    for r in rows:
        lines.append(
            f"{r.model:<38} {r.calls:>5} {r.tokens:>7} ${r.cost_usd:>10.6f} "
            f"${r.cost_usd / r.calls:>9.6f} {r.mean_latency_s:>12.2f}s"
        )
    if len(rows) > 1 and rows[0].cost_usd > 0:
        lines.append(f"\n{rows[-1].model} costs {rows[-1].cost_usd / rows[0].cost_usd:.1f}x {rows[0].model}")
    return "\n".join(lines)
