"""Command line: `review-router run` sends the diffs to every model and prints the comparison."""

import argparse

from review_router.config import DEFAULT_MODELS
from review_router.diffs import load_diffs
from review_router.report import render_table, summarize
from review_router.router import run_all


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="review-router", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="review the sample diffs with every model")
    run.add_argument("--model", action="append", dest="models", help="LiteLLM model string; repeatable")
    run.add_argument("--diff", action="append", dest="diffs", help="only diffs whose name contains this; repeatable")
    run.add_argument("--show", action="store_true", help="print each model's review text")
    return parser


def cmd_run(args: argparse.Namespace) -> int:
    models = args.models or DEFAULT_MODELS
    diffs = load_diffs(only=args.diffs)
    if not diffs:
        print("no diffs matched")
        return 1
    reviews = run_all(models, diffs)
    for r in reviews:
        print(f"{r.model:<38} {r.diff:<22} {r.latency_s:5.2f}s ${r.cost_usd:.6f} {r.tokens:4d} tok")
        if args.show:
            print("    " + r.summary.replace("\n", "\n    "))
    print()
    print(render_table(summarize([(r.model, r.latency_s, r.cost_usd, r.tokens) for r in reviews])))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return {"run": cmd_run}[args.command](args)
