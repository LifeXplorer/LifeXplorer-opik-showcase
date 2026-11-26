"""Chess-openings QA: compare an uncompiled and a compiled DSPy program."""

import os

# Drop base-URL overrides so the example talks to the public API.
for var in ("OPENAI_BASE_URL", "OPENAI_API_BASE"):
    os.environ.pop(var, None)

import dotenv
import dspy

from chess_qa.compiling import compile_program
from chess_qa.examples import testset
from chess_qa.handbook import HANDBOOK
from chess_qa.metric import house_format_metric
from chess_qa.program import build_program

MODEL = "openai/gpt-4o-mini"


def pass_rate(program) -> float:
    evaluate = dspy.Evaluate(devset=testset, metric=house_format_metric,
                             num_threads=4, display_progress=False)
    return float(evaluate(program).score) / 100


def main() -> None:
    dotenv.load_dotenv(dotenv.find_dotenv())
    dspy.configure(lm=dspy.LM(MODEL, cache=False))

    program = build_program()
    question = "What does White play on move 3 of the Italian Game?"
    print(f"Q: {question}")
    print(f"A (uncompiled): {program(context=HANDBOOK, question=question).answer}\n")

    print("Compiling with BootstrapFewShot...")
    compiled = compile_program(program)

    print(f"uncompiled: {pass_rate(program):.0%} pass rate")
    print(f"compiled:   {pass_rate(compiled):.0%} pass rate")


if __name__ == "__main__":
    main()
