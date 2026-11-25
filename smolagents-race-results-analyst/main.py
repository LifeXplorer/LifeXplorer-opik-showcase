"""Ask a smolagents CodeAgent questions about a marathon results CSV and grade its answers."""

from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

# Provider keys live in the repo-root .env (a local .env works too). Load them before
# anything reads the environment.
load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent / ".env")

from smolagents import CodeAgent, OpenAIModel  # noqa: E402

from analysis import CSV_PATH, check_answer, expected_answers, load_rows  # noqa: E402
from feedback import SCORE_NAME, attach_scores  # noqa: E402
from tracing import setup_tracing  # noqa: E402

PROJECT_NAME = "smolagents-race-results-analyst"

BRIEFING = f"""\
You are the results analyst for the Saltmarsh Coastal Marathon 2025.
The results are in the CSV file at: {CSV_PATH}

Columns: bib, runner, gender (F/M), age_group, club, half_split and chip_time
(both H:MM:SS text; chip_time is empty when status is DNF), status (FIN or DNF).
A negative split means the second half was faster than the first half.

Load it with pandas and answer with concrete numbers from the data. Give the final
answer as one or two plain sentences, not as a raw Python object.
"""

QUESTIONS = [
    "Who won the women's 40-44 age group, and what was her chip time?",
    "Which club has the highest percentage of finishers who ran a negative split? "
    "Only consider clubs with at least 5 finishers, and give the percentage rounded to one decimal.",
    "Which age group has the highest DNF rate (DNF starters divided by all starters)? "
    "Give the rate as a percentage rounded to one decimal.",
]


def build_agent() -> CodeAgent:
    # A CodeAgent answers by writing Python and running it in smolagents' local executor;
    # pandas is the only import allowed beyond the safe defaults.
    return CodeAgent(
        tools=[],
        model=OpenAIModel(model_id="gpt-4o-mini"),
        additional_authorized_imports=["pandas"],
        max_steps=8,
    )


def ask(agent: CodeAgent, question: str) -> str:
    # One agent.run = one Opik trace; the question is part of the task input,
    # which is how the grade below finds its trace again.
    return str(agent.run(BRIEFING + "\nQuestion: " + question))


def main() -> None:
    provider = setup_tracing(PROJECT_NAME)
    started = datetime.now(UTC)
    agent = build_agent()
    expected = expected_answers(load_rows())
    verdicts: dict[str, list[str]] = {}
    correct = 0
    for i, (question, exp) in enumerate(zip(QUESTIONS, expected, strict=True), 1):
        print(f"\n{'=' * 72}\nQuestion {i}: {question}\n{'=' * 72}")
        answer = ask(agent, question)
        problems = check_answer(answer, exp)
        verdicts[question] = problems
        correct += not problems
        print(f"\nAnswer {i}: {answer}\nGrade: {'correct' if not problems else 'WRONG ' + '; '.join(problems)}")
    print(f"\n{correct}/{len(QUESTIONS)} answers match the ground truth.")

    if provider is None:
        return
    # Shut the provider down so any buffered spans are exported before the process exits.
    provider.shutdown()
    print(f"Scored {attach_scores(PROJECT_NAME, started, verdicts)} traces with '{SCORE_NAME}'.")
    print(f"Open the '{PROJECT_NAME}' project in Opik: one trace per question.")


if __name__ == "__main__":
    main()
