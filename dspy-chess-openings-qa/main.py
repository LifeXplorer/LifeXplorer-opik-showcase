"""Chess-openings QA: run one Opik test suite against an uncompiled and a compiled DSPy program."""

import os

# Drop base-URL overrides so the example talks to the public API.
for var in ("OPENAI_BASE_URL", "OPENAI_API_BASE"):
    os.environ.pop(var, None)

import dotenv
import dspy
import opik

from chess_qa.compiling import compile_program
from chess_qa.handbook import HANDBOOK
from chess_qa.program import ask, build_program
from chess_qa.suite import get_suite, run_suite
from chess_qa.tracing import PROJECT_NAME, install_opik_callback

MODEL = "openai/gpt-4o-mini"


def main() -> None:
    dotenv.load_dotenv(dotenv.find_dotenv())
    dspy.configure(lm=dspy.LM(MODEL, cache=False))
    install_opik_callback()

    program = build_program()
    question = "What does White play on move 3 of the Italian Game?"
    print(f"Q: {question}")
    print(f"A (uncompiled): {ask(program, HANDBOOK, question)}\n")

    suite = get_suite(opik.Opik())

    print("Running the suite against the uncompiled program...")
    before = run_suite(suite, program, "dspy-uncompiled",
                       {"program": "ChainOfThought(OpeningQA)", "compiled": False, "model": MODEL})

    print("\nCompiling with BootstrapFewShot...")
    compiled = compile_program(program)

    print("\nRunning the same suite against the compiled program...")
    after = run_suite(suite, compiled, "dspy-compiled",
                      {"program": "ChainOfThought(OpeningQA)", "compiled": True,
                       "optimizer": "BootstrapFewShot", "model": MODEL})

    print("\n=== Uncompiled vs compiled ===")
    for label, result in (("uncompiled", before), ("compiled  ", after)):
        print(f"{label}: {result.pass_rate:.0%} pass rate "
              f"({result.items_passed}/{result.items_total} items passed)")

    # Traces are sent from a background thread; flush so none are lost at exit.
    opik.flush_tracker()
    print(f"\nTraces: project {PROJECT_NAME!r} in Opik (http://localhost:5173)")
    if after.experiment_url:
        print(f"Runs: {after.experiment_url}")


if __name__ == "__main__":
    main()
