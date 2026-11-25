# pydantic-ai-recipe-extraction

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Pydantic AI](https://img.shields.io/badge/pydantic--ai-2.31%2B-E92063?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.2%2B-2f54eb?style=flat)

**A typed recipe card that looks perfect, and a test suite that checks whether the model made any of it up.**

Grandma's pancake note says "~2 min a side". Your extractor returns `cook_minutes: 2`. Looks fine; it is
wrong (it is two minutes per side, not the cook time). A typed schema guarantees the *shape* of the output and
says nothing about whether the *values* came from the note. This example extracts `RecipeCard`s from five
messy home-cook notes and then checks, two ways, that nothing was invented.

## What you'll build

- A Pydantic AI agent (`gpt-4o-mini`, `output_type=RecipeCard`). Servings, prep and cook minutes, oven
  temperature, credit and every ingredient quantity are optional, because real notes rarely state them all.
- Tracing through OpenTelemetry: Pydantic AI emits spans via logfire, and Opik's `OpikSpanProcessor` ships them
  to Opik's OTLP endpoint and nests them under one `@opik.track` trace per extraction. No Opik-specific
  model wrapper.
- A deterministic `grounding.py` that compares every number and ingredient on the card with the note and logs the
  result as a `grounded` feedback score on the trace.
- An Opik test suite of the same five notes: three global rules ("every number appears in the note", "no
  ingredient is added from cooking knowledge", "unstated fields are null") plus two or three assertions per note
  ("oven_temp_c is 175", "yoghurt is not listed, the note says not to add it"). An LLM judge scores each
  assertion; a note passes only if all of them do.

## See it in Opik

Open the `pydantic-ai-recipe-extraction` project at http://localhost:5173 (or your Opik Cloud workspace).

- **Traces tab.** One run leaves 10 traces: five named `extract_recipe` from the first loop, and five named
  `evaluation_task` from the test suite (each wraps another `extract_recipe`). Expand an `extract_recipe` trace
  and you see `invoke_agent agent` with a `chat gpt-4o-mini` child, typed `llm`, carrying the model name,
  prompt/completion tokens (322 / 136 in our run) and an estimated cost of about $0.00013. Input is the raw
  note; output is the full card.
- **`grounded` column.** Each trace carries a `grounded` feedback score, 1.0 or 0.0, with the reason as
  its tooltip. In our run the lemon-bars trace scored 0.0 with the reason `cook_minutes=45 is not in the note`:
  the note says "bake base 20 min then filling 25 min", and the model quietly added them. Filter the
  column to 0 to get a list of suspicious extractions without reading any of them.
- **Test Suites tab, then the run.** The suite `pydantic-ai-recipe-extraction` holds five items. The run
  `recipe-extraction-gpt-4o-mini` scored 80% (4/5) in our run. Banana bread failed: the note says "bake ~55 min" and the
  assertion `oven_temp_c is 175 and cook_minutes is 55` wants both, but the card had `cook_minutes: null`. Open
  the item to see each assertion with the judge's pass/fail and its reason.
- **The two checks disagree, usefully.** The judge accepted lemon bars' 45 minutes as "derivable from the note";
  the strict string check flagged it. Decide which behaviour you want, then change the assertion wording or the checker.
  Results vary between runs: we saw 60% and 80% for the same code.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and have an Opik instance (local: `http://localhost:5173`, or Opik Cloud).
2. `cp .env.example .env`, add `OPENAI_API_KEY`, and set the Opik variables (or run `opik configure`). The app also finds a `.env` in any parent folder.
3. `uv sync`
4. `uv run main.py`
5. Open the project and the experiment link printed at the end. A run costs well under a cent in agent calls, plus a few cents for the judge.
6. `uv run pytest` runs the offline tests.

## Poke around

- Delete "Never add ingredients or numbers the note lacks" from `SYSTEM_PROMPT` and re-run: watch
  the `grounded` column and the "no ingredient is added" global rule start failing.
- Swap `gpt-4o-mini` for `gpt-4o` in `build_agent` and re-run. Each run is a new experiment on the same
  suite, so pass rates compare directly.
- Add your own worst note to `data/notes.json` with assertions in plain language. Suite inserts deduplicate, so only your note is added.
- Loosen `find_ungrounded` to accept sums of stated numbers and see lemon bars turn green on the trace but not
  necessarily in the judge.

## Gotchas we hit

- **Symptom:** a `chat test` span appears in the project after `uv run pytest`, even though tests stub the model.
  **Cause:** `OPIK_TRACK_DISABLE=true` only stops `@opik.track`; the logfire/OTel exporter keeps sending
  Pydantic AI spans. **Fix:** also set `OTEL_SDK_DISABLED=true` before importing `recipes`, as `tests/test_extract.py` does.
- **Symptom:** the project holds 10 traces for 5 notes. **Cause:** `run_tests` calls your task once per note, wrapped in an
  `evaluation_task` trace, on top of the five direct extractions in `main.py`. **Fix:** nothing to fix; filter by
  trace name, and delete earlier traces before re-running if you want clean counts.
- **Symptom:** nothing reaches Opik although the agent runs. **Cause:** the OTLP endpoint and headers
  must be in the environment before `logfire.configure()`. **Fix:** call `configure_opik_otel()` first, as
  `recipes.py` does; it sets `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_EXPORTER_OTLP_HEADERS` (`Comet-Workspace`,
  `projectName`, and `Authorization` only when an API key exists).

## How it's put together

- `recipes.py`: OTel setup, `RecipeCard` schema, agent, and the traced `extract_recipe` that scores `grounded`.
- `grounding.py`: offline check that numbers and ingredients on a card appear in the note.
- `main.py`: extracts the notes, builds the test suite, runs it and flushes.
- `data/notes.json`: five fictional notes with their per-note assertions.
- `tests/test_grounding.py`: invented numbers, ingredients, quantities, Fahrenheit, abbreviations.
- `tests/test_extract.py`: runs the traced function against a stub model with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
