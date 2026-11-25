# Wedding-Day Planner Crew

**`crewai-wedding-planner`**: three CrewAI agents draft a run of show, and Opik prices each one.

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![CrewAI](https://img.shields.io/badge/crewai-1.15%2B-FF5A50?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.2%2B-2f54eb?style=flat)

---

A crew hands you a finished plan and nothing else. You can't tell which agent produced which part, what each one was given, or who spent the tokens. Here a Budget Coordinator, a Timeline Planner and a Guest Experience Editor plan a fictional wedding (Marisol and Teodor, 90 guests, an orchard barn with a 22:30 music curfew and a 23:15 last shuttle). One call to `track_crewai` turns each `kickoff()` into a single Opik trace, with tokens and dollars on every agent.

## What you'll build

- A sequential crew on `gpt-4o-mini`: budget review, then timeline, then a merged final plan. Each task receives the earlier outputs as context.
- `data/wedding_brief.md`, the offline fictional brief. No search tools, so only an OpenAI key is needed.
- `planning.py`, plain Python that does the arithmetic (plates, shuttle runs) and hands the agents a ready-made budget snapshot, plus `check_plan`, which flags a final plan whose timeline is out of order or runs past the last shuttle.
- `report_costs.py`, which reads the newest trace back from Opik and prints tokens and cost per agent.

## See it in Opik

Open the project `crewai-wedding-planner`. The Traces tab has one row for the run, named `kickoff`: its input is the brief and budget snapshot, its output the finished plan, and its usage shows 3,742 tokens and about $0.0012. Expand it and you get 49 spans: three `Task: ...` spans (Review the budget, Build the timeline, Write the wedding-day plan), a span for each agent role under its task, and under each agent the planning steps CrewAI runs internally. Only three of those spans are type `llm` (`chat_completion_create`, one per agent), and they carry the usage and cost.

In the verified run:

| Agent | LLM calls | Tokens | Cost |
|---|---|---|---|
| Budget Coordinator | 1 | 888 | $0.00024 |
| Timeline Planner | 1 | 1,296 | $0.00040 |
| Guest Experience Editor | 1 | 1,558 | $0.00056 |
| Total | 3 | 3,742 | $0.00120 |

The editor costs most because it reads both upstream outputs. Click its llm span to see exactly that context in the input.

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY` (a `.env` in a parent folder also works). Leave the Opik settings empty to use `~/.opik.config`, or set `OPIK_URL_OVERRIDE` / `OPIK_WORKSPACE`.
2. `uv sync`
3. `uv run main.py` (a minute or two, roughly a tenth of a cent).
4. `uv run python report_costs.py` to print the per-agent table above from Opik.
5. Offline tests: `OPIK_TRACK_DISABLE=true uv run pytest` (no keys needed).

## Poke around

- Put `llm="gpt-4o"` on the editor only and compare its row in `report_costs.py` against the other two.
- Edit `data/wedding_brief.md` (say, move the last shuttle earlier) and see whether `Plan checks:` at the end of the run catches a timeline that ignores it.
- Open the Timeline Planner's llm span and compare the brief it received with the times it produced.
- Add a fourth agent (a vendor liaison) with its own task and watch a new branch appear under the trace with no Opik changes.

## Gotchas we hit

- **Symptom:** the trace has spans but none of type `llm`, and no tokens or cost anywhere. **Cause:** on CrewAI 1.x, `track_crewai(project_name=...)` alone does not capture the model calls. **Fix:** pass the crew, `track_crewai(project_name=PROJECT, crew=crew)`. Without it a one-agent test run produced 16 spans and zero llm spans.
- **Symptom:** `report_costs.py` shows costs on spans but you can't tell which agent they belong to. **Cause:** cost lives on the `chat_completion_create` span, several levels below the agent span. **Fix:** walk `parent_span_id` upward until the parent's name starts with `Task: ` (see `agent_of`).

## How it's put together

- `main.py`: agents, tasks, the crew, `track_crewai`, and the final flush.
- `planning.py`: budget and shuttle arithmetic, and the `check_plan` guardrail.
- `report_costs.py`: reads the latest trace from Opik and rolls up cost per agent.
- `data/wedding_brief.md`: the fictional brief.
- `tests/test_planning.py`: offline tests for the helpers, plus an import of the traced crew with tracking disabled.

*built with Opik · inspired by Opik's examples and documentation*
