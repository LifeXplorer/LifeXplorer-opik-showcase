"""Ask the syllabi a few policy questions and print the answers with their sources."""

import logging
import os

import dotenv

dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True))  # walks up to a repo-root .env if there is one

import opik  # noqa: E402

os.environ.setdefault("LITELLM_LOG", "ERROR")  # the judge calls LiteLLM; keep its per-call INFO lines out of the output
logging.getLogger().setLevel(logging.WARNING)  # same for httpx request lines
for noisy in ("LiteLLM", "httpx"):
    logging.getLogger(noisy).setLevel(logging.ERROR)

from syllabus_qa import engine, questions, suite, tracing  # noqa: E402


def main() -> None:
    tracing.enable_tracing()
    query_engine = engine.build_query_engine()
    for question in questions.DEMO_QUESTIONS:
        answer = engine.ask(query_engine, question)
        print(f"Q: {question}\nA: {answer.text}")
        print("   sources: " + ", ".join(f"{s['file']} ({s['score']})" for s in answer.sources) + "\n")

    # Policy suite: 8 rules x 3 runs, scored by Opik's LLM judge. Shows up under Test suites.
    client = opik.Opik()
    result = suite.run_suite(query_engine, client)
    print("\n".join(suite.summarize(result)))
    if result.experiment_url:
        print(f"\nView the run: {result.experiment_url}")

    # Traces are sent from a background thread; flush so none are lost when the script exits.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
