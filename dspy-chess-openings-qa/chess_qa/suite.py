"""The Opik test suite and the two runs compared in the lesson."""

import dspy
import opik

from .examples import TEST_ROWS
from .handbook import HANDBOOK
from .program import ask
from .tracing import PROJECT_NAME

SUITE_NAME = "dspy-chess-openings-qa"

# Plain-language bar that an LLM judge checks on every item.
GLOBAL_ASSERTIONS = [
    "The answer ends with a card tag of the exact form '| card: <CARD-ID>' "
    "citing exactly one card id, such as ITA-1",
    "The card id cited in the answer is the opening card that actually "
    "contains the answer",
    "Apart from the card tag, the answer is a single short phrase or sentence "
    "that directly gives the requested fact, with no surrounding explanation",
]


def get_suite(client: opik.Opik):
    """Create (or fetch) the test suite and insert the held-out questions.

    A test suite pairs each item with its own assertions; the global ones above
    apply to every item. It shows up under the project's test suites, and each
    run_tests call adds one run to it, so both programs face identical checks.
    """
    suite = client.get_or_create_test_suite(
        name=SUITE_NAME,
        project_name=PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
    )
    # insert skips items identical to ones already stored, so re-running is safe;
    # an item whose assertion text you edit counts as new and is added alongside the old one.
    suite.insert([
        {"data": {"question": question, "card": card},
         "assertions": [assertion]}
        for question, card, _fact, assertion in TEST_ROWS
    ])
    return suite


def make_task(program: dspy.Module):
    """Wrap a program as a run_tests task: item in, {input, output} out."""

    def task(item: dict) -> dict:
        return {"input": {"question": item["question"]},
                "output": ask(program, HANDBOOK, item["question"])}

    return task


def run_suite(suite, program: dspy.Module, name: str, config: dict):
    """Run the suite against one program as an Opik experiment named `name`.

    experiment_config is stored on the run, so the runs list shows which one
    was compiled. Each item also produces a trace in the project.
    """
    return opik.run_tests(
        test_suite=suite,
        task=make_task(program),
        experiment_name=name,
        experiment_config=config,
        worker_threads=4,
        generate_report=False,
    )
