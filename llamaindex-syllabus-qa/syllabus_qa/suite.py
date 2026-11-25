"""A policy-level Opik test suite: each item is a rule a student could rely on."""

import opik

from syllabus_qa import corpus, engine
from syllabus_qa.tracing import PROJECT_NAME

SUITE_NAME = "syllabus-policies"

# Rules that must hold for every answer, judged against the answer AND the retrieved excerpts.
GLOBAL_ASSERTIONS = [
    "Every percentage, day count, time and number in the answer appears in the retrieved "
    "excerpts, or is plain arithmetic on a retrieved rate (10% per 24 hours over 48 hours "
    "is 20%): the answer invents no figures.",
    "Each rule is attributed to the course code it comes from, and no course's rule is "
    "applied to another course.",
]

# One item per policy question. `assertions` pin the exact facts the answer must state.
SUITE_ITEMS = [
    {
        "question": "In BIO 214, how much of the mark is lost if a lab report is 48 hours late, "
                    "and when does it stop being accepted?",
        "assertions": [
            "The answer says a BIO 214 lab report 48 hours late loses 20% of its mark",
            "The answer says a BIO 214 lab report more than 3 days late gets zero",
        ],
    },
    {
        "question": "How do slip days work in CS 330?",
        "assertions": [
            "The answer says CS 330 gives each student 4 slip days for the term, at most 2 per assignment",
            "The answer says that after slip days run out CS 330 deducts 20% per day",
        ],
    },
    {
        "question": "What happens if I hand in an HIS 101 essay late and have no extension token?",
        "assertions": [
            "The answer says HIS 101 deducts a flat 15%",
            "The answer says nothing is accepted more than 7 days late in HIS 101",
        ],
    },
    {
        "question": "Which course bans AI tools for anything I submit?",
        "assertions": [
            "The answer names HIS 101 as the course that prohibits AI tools for submitted writing",
            "The answer does not say that BIO 214 or CS 330 prohibits AI tools entirely",
        ],
    },
    {
        "question": "I missed a BIO 214 field trip and did not tell anyone. What does it cost me?",
        "assertions": [
            "The answer says missing a BIO 214 field trip without 48 hours' notice costs 5% of the final grade",
        ],
    },
    {
        "question": "What happens to my HIS 101 grade if I skip more than four classes without an excuse?",
        "assertions": [
            "The answer says the HIS 101 final grade drops by one letter step",
        ],
    },
    {
        "question": "How is CS 330 graded?",
        "assertions": [
            "The answer gives CS 330 weights of 30% problem sets, 30% projects, 15% midterm and 25% final",
        ],
    },
    {
        # The syllabi say "no extra credit" for CS 330 and HIS 101 only. A good answer admits
        # BIO 214 is silent instead of borrowing a neighbour's sentence.
        "question": "Is there extra credit in BIO 214?",
        "assertions": [
            "The answer says the BIO 214 syllabus does not specify extra credit",
            "The answer does not claim BIO 214 offers extra credit",
        ],
    },
]


def courses_in(sources: list[dict]) -> list[str]:
    """Map retrieved chunks to course codes, in retrieval order, without repeats."""
    by_file = {s.filename: s.code for s in corpus.SYLLABI}
    codes: list[str] = []
    for source in sources:
        code = by_file.get(source["file"], source["file"])
        if code not in codes:
            codes.append(code)
    return codes


def make_task(query_engine):
    """Wrap the query engine as the function the suite runs for every item."""

    def task(item: dict) -> dict:
        answer = engine.ask(query_engine, item["question"])
        return {
            "input": item,
            # The judge sees the excerpts next to the answer, so it can check that the
            # figures in the answer were actually retrieved.
            "output": {
                "answer": answer.text,
                "retrieved_courses": courses_in(answer.sources),
                "retrieved_excerpts": [s["text"] for s in answer.sources],
            },
        }

    return task


def build_suite(client: opik.Opik):
    """Create the suite (or fetch it) and make sure every item is in it."""
    # The suite is stored in Opik as a dataset with assertions; project_name ties its
    # runs to the same project as the traces. runs_per_item=3 / pass_threshold=2 lets an
    # item pass when the judge agrees 2 of 3 times, so one flaky verdict doesn't fail it.
    suite = client.get_or_create_test_suite(
        name=SUITE_NAME,
        project_name=PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
        global_execution_policy={"runs_per_item": 3, "pass_threshold": 2},
    )
    # insert() de-duplicates identical items, so re-running does not grow the suite.
    suite.insert(
        [{"data": {"question": i["question"]}, "assertions": i["assertions"]} for i in SUITE_ITEMS]
    )
    return suite


def run_suite(query_engine, client: opik.Opik):
    """Run every policy through the engine and let Opik's LLM judge check the assertions."""
    # run_tests executes the task per item (x3 runs), has the judge score each assertion,
    # and records one experiment run with pass/fail per item. No `model=` override: a judge
    # model passed with reasoning_effort is rejected by the endpoint.
    return opik.run_tests(
        test_suite=build_suite(client),
        task=make_task(query_engine),
        experiment_name="gpt-4o-mini-top4",
        experiment_config={"llm": "gpt-4o-mini", "top_k": engine.TOP_K},
        worker_threads=4,
        verbose=0,
        generate_report=False,  # skip the local JSON report file; the run lives in Opik
    )


def summarize(result) -> list[str]:
    """One printable line per item, plus the failing assertions."""
    lines = [f"Pass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} items)"]
    for item in result.item_results.values():
        first = item.test_results[0].test_case.task_output
        mark = "PASS" if item.passed else "FAIL"
        lines.append(f"  [{mark}] {item.runs_passed}/{item.runs_total} runs  {first['input']['question']}")
        if not item.passed:
            for run in item.test_results:
                for score in run.score_results:
                    if score.scoring_failed or score.value != 1:
                        lines.append(f"      failed: {score.name}: {score.reason}")
    return lines
