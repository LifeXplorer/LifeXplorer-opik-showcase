"""Three-agent wedding-day planning crew, traced with Opik.

A budget coordinator, a day-of timeline planner and a guest-experience editor
run in sequence on gpt-4o-mini. The brief is a fictional file (data/wedding_brief.md),
so the run needs only an OpenAI key. Opik logs the whole kickoff as ONE trace.
"""

from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Load the repo-root .env before crewai / opik read their keys.
load_dotenv(find_dotenv(usecwd=True))

import opik
from crewai import Agent, Crew, Process, Task
from opik.integrations.crewai import track_crewai

from planning import budget_snapshot, check_plan

# The Opik project is named after the folder, so every trace lands in one place.
PROJECT = "crewai-wedding-planner"
MODEL = "gpt-4o-mini"
BRIEF = (Path(__file__).resolve().parent / "data" / "wedding_brief.md").read_text()

coordinator = Agent(
    role="Budget Coordinator",
    goal="Check the vendor list against the budget and flag anything that risks it.",
    backstory="An event producer who trusts the numbers you are given and never recalculates them.",
    llm=MODEL,
)
timeline_planner = Agent(
    role="Timeline Planner",
    goal="Build a minute-accurate run of show that respects every venue constraint.",
    backstory="A day-of coordinator who works backwards from sunset, curfews and the last shuttle.",
    llm=MODEL,
)
editor = Agent(
    role="Guest Experience Editor",
    goal="Merge budget notes and timeline into one plan the couple can read in five minutes.",
    backstory="A warm but exact editor who keeps every time and dollar figure intact.",
    llm=MODEL,
)

budget_task = Task(
    name="Review the budget",
    description=(
        "Using ONLY the brief and the budget snapshot, review spending.\n\n"
        "BRIEF:\n{brief}\n\nBUDGET SNAPSHOT (already calculated):\n{budget}"
    ),
    expected_output="4-6 bullets: where the money goes, headroom, and two risks (allergies, rain plan).",
    agent=coordinator,
)
timeline_task = Task(
    name="Build the timeline",
    description=(
        "Build the wedding-day run of show from vendor load-in to the last shuttle. "
        "Every line must start with a 24-hour time like '16:00 - ...', in chronological "
        "order, and mention the 22:30 music curfew.\n\nBRIEF:\n{brief}"
    ),
    expected_output="At least 12 lines, each 'HH:MM - activity (owner)'.",
    agent=timeline_planner,
    context=[budget_task],
)
plan_task = Task(
    name="Write the wedding-day plan",
    description=(
        "Combine the budget review and the timeline into a final plan with sections "
        "Budget, Timeline, Dietary and access, Rain plan. Keep the timeline lines as "
        "'HH:MM - activity' unchanged."
    ),
    expected_output="A plan under 450 words, plain text.",
    agent=editor,
    context=[budget_task, timeline_task],
)

crew = Crew(
    agents=[coordinator, timeline_planner, editor],
    tasks=[budget_task, timeline_task, plan_task],
    process=Process.sequential,
    verbose=False,
)

# track_crewai logs each kickoff as one trace (crew -> task -> agent -> llm spans, with
# token usage and cost on the llm spans). Passing crew= is required on CrewAI >= 1.0,
# otherwise the LLM calls are not captured.
track_crewai(project_name=PROJECT, crew=crew)


def run() -> str:
    inputs = {"brief": BRIEF, "budget": budget_snapshot(adults=84, children=6, riding=40)}
    result = str(crew.kickoff(inputs=inputs))
    problems = check_plan(result)
    print(result)
    print("\nPlan checks:", "all passed" if not problems else "; ".join(problems))
    # Short-lived scripts must flush, or buffered spans are lost when the process exits.
    opik.flush_tracker()
    print(f"\nOpen http://localhost:5173 -> project '{PROJECT}'")
    return result


if __name__ == "__main__":
    run()
