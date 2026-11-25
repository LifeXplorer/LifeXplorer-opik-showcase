"""Extract recipe cards from messy notes, trace them, and run the invented-value test suite."""

import json
from pathlib import Path
from typing import Any

import logfire
import opik

from grounding import find_ungrounded
from recipes import PROJECT_NAME, extract_recipe

NOTES = json.loads((Path(__file__).parent / "data" / "notes.json").read_text())

# Rules every card must satisfy, judged in plain language.
GLOBAL_ASSERTIONS = [
    "Every number on the card (servings, minutes, temperature, quantities) appears in, or is directly derivable from, the note",
    "Every ingredient on the card is mentioned in the note; none is added from general cooking knowledge",
    "Fields the note does not state are null rather than guessed",
]

# The data holds only the note; expected values live in assertions so the
# judge cannot read answers off the input.
SUITE_ITEMS = [{"data": {"text": n["text"]}, "assertions": n["assertions"]} for n in NOTES]


def main() -> None:
    print(f"Extracting {len(NOTES)} notes with gpt-4o-mini...\n")
    for note in NOTES:
        card = extract_recipe(note["text"])
        problems = find_ungrounded(card, note["text"])
        print(f"{note['id']:12s} {'OK' if not problems else 'INVENTED: ' + '; '.join(problems)}")

    client = opik.Opik()
    # A test suite = items + plain-language assertions; Opik's LLM judge scores each item pass/fail.
    suite = client.get_or_create_test_suite(
        name=PROJECT_NAME, project_name=PROJECT_NAME, global_assertions=GLOBAL_ASSERTIONS
    )
    suite.insert(SUITE_ITEMS)

    def task(item: dict[str, Any]) -> dict[str, Any]:
        return {"input": item, "output": extract_recipe(item["text"])}

    # run_tests creates an experiment: one row per note, pass only if all assertions hold.
    result = opik.run_tests(
        test_suite=suite,
        task=task,
        experiment_name="recipe-extraction-gpt-4o-mini",
        worker_threads=4,
        generate_report=False,
    )
    print(f"\nPass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total})")
    for r in result.item_results.values():
        text = r.test_results[0].test_case.task_output["input"]["text"]
        print(f"  [{'PASS' if r.passed else 'FAIL'}] {text[:60]!r}")
    print(f"\nExperiment: {result.experiment_name} ({result.experiment_url})")

    # Flush both pipelines: OTel spans (logfire) and Opik's own queue (traces, experiment items).
    logfire.force_flush()
    client.flush()
    opik.flush_tracker()


if __name__ == "__main__":
    main()
