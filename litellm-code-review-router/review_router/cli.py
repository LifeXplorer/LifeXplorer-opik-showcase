"""Command line: `review-router run` sends the diffs to every model and prints the comparison."""

import argparse
import uuid

from review_router.config import DEFAULT_MODELS
from review_router.diffs import load_diffs
from review_router.report import render_table, summarize
from review_router.opik_report import fetch_samples
from review_router.router import run_all
from review_router.tracing import flush, setup_tracing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="review-router", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="review the sample diffs with every model")
    run.add_argument("--model", action="append", dest="models", help="LiteLLM model string; repeatable")
    run.add_argument("--diff", action="append", dest="diffs", help="only diffs whose name contains this; repeatable")
    run.add_argument("--show", action="store_true", help="print each model's review text")
    compare = sub.add_parser("compare", help="rebuild the comparison table from what Opik recorded for a run")
    compare.add_argument("run_id", help="the run id printed by `review-router run`")
    return parser


def cmd_run(args: argparse.Namespace) -> int:
    models = args.models or DEFAULT_MODELS
    diffs = load_diffs(only=args.diffs)
    if not diffs:
        print("no diffs matched")
        return 1
    run_id = uuid.uuid4().hex[:8]
    setup_tracing()
    reviews = run_all(models, diffs, run_id)
    flush()
    for r in reviews:
        print(f"{r.model:<38} {r.diff:<22} {r.latency_s:5.2f}s ${r.cost_usd:.6f} {r.tokens:4d} tok")
        if args.show:
            print("    " + r.summary.replace("\n", "\n    "))
    print()
    print(render_table(summarize([(r.model, r.latency_s, r.cost_usd, r.tokens) for r in reviews])))
    print(f"\nrun id: {run_id}  ->  uv run review-router compare {run_id}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    samples = fetch_samples(args.run_id)
    if not samples:
        print(f"no llm spans found in Opik for run {args.run_id}")
        return 1
    print(render_table(summarize(samples)))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return {"run": cmd_run, "compare": cmd_compare}[args.command](args)
