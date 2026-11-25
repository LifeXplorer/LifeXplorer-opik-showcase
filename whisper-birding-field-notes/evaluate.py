"""Test suite for the sighting extractor, with a judge tamed by execution_policy.

Replays each transcript saved by main.py through the extract + clean steps and
asks an LLM judge two questions about the resulting log. The judge reads an
imperfect transcript, so single verdicts flip; each item runs three times and
must pass twice.
"""

import json
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))
os.environ["OPIK_PROJECT_NAME"] = "whisper-birding-field-notes"
os.environ.pop("OPENAI_BASE_URL", None)

import opik

from birding.pipeline import extract_sightings
from birding.sightings import clean_sightings, load_checklist

OUT_DIR = Path(__file__).resolve().parent / "out"
SUITE_NAME = "birding-sighting-log-suite"

ASSERTIONS = [
    "Every species in the sighting log is one the observer actually saw or "
    "heard in the transcript. A species the observer retracted (for example "
    "'scratch that') must not appear.",
    "Every count in the log matches the number the observer gave in the "
    "transcript, and a species mentioned without a number is logged as 1.",
]


def task(item: dict) -> dict:
    # The suite calls this once per run; each call lands as an "evaluation_task"
    # trace in the project, with the traced extract-sightings span inside it.
    sightings = clean_sightings(extract_sightings(item["transcript"]), load_checklist())
    return {
        "input": {"transcript": item["transcript"]},
        "output": {"sightings": [{k: s[k] for k in ("species", "count", "note")} for s in sightings]},
    }


if __name__ == "__main__":
    records = [json.loads(p.read_text()) for p in sorted(OUT_DIR.glob("*.json"))]
    if not records:
        raise SystemExit("No transcripts in out/ - run `uv run main.py` first.")

    client = opik.Opik()
    # get_or_create_test_suite makes a suite whose global assertions are
    # checked by an LLM judge on every item; it appears under Test suites.
    suite = client.get_or_create_test_suite(
        name=SUITE_NAME,
        project_name="whisper-birding-field-notes",
        global_assertions=ASSERTIONS,
        # runs_per_item=3 / pass_threshold=2 gives each item three independent
        # runs and passes it on a 2-of-3 majority, absorbing one-off judge flips.
        global_execution_policy={"runs_per_item": 3, "pass_threshold": 2},
    )
    existing = {i["data"]["note"] for i in suite.get_items()}
    for r in records:
        if r["note"] not in existing:
            suite.insert([{"data": {"note": r["note"], "transcript": r["transcript"]}}])

    # run_tests executes task on every item and creates an experiment with a
    # pass/fail verdict and judge reason per assertion.
    result = opik.run_tests(test_suite=suite, task=task)
    print(f"\nPass rate: {result.pass_rate:.0%}")
    opik.flush_tracker()
