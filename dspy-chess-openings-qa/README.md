# dspy-chess-openings-qa

*A DSPy program that writes its own few-shot prompt, and an Opik test suite that shows what the prompt bought: 0 of 8 items before, 7 of 8 after.*

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![DSPy 3](https://img.shields.io/badge/DSPy-3.x-8B0000)
![Opik SDK 2.3](https://img.shields.io/badge/Opik%20SDK-2.3-2f54eb)

A prompt optimizer can claim a win, but it can't show you what changed. This example puts a number and a diff behind the claim: the same eight questions are graded before and after DSPy compiles the program, and both runs sit side by side in Opik.

## The problem

Rookfield Chess Club (fictional) keeps a binder of opening cards for its junior coaches. Coaches answer questions in a house style: the bare answer, then a card tag, like `e3 and c3 | card: LON-1`. Nobody wrote that rule into the prompt. It exists only in past answers. A plain DSPy program doesn't know it, so it answers in correct, chatty prose with no card tag. Every fact is right and every answer is rejected.

## What you'll build

- `OpeningQA`, a `dspy.ChainOfThought` over the eight cards in `chess_qa/handbook.py`. Its signature says only "answer the coach's question".
- `compiling.py`, which runs `dspy.BootstrapFewShot` over eight worked tickets (`chess_qa/examples.py`). A regex metric keeps only teacher attempts that end in the right `| card: ID` tag and mention the key fact, so compiling spends no judge tokens.
- `suite.py`, an Opik test suite of eight held-out questions. Three global assertions (card tag, right card, short answer) plus one fact assertion per item are checked by an LLM judge. The suite runs twice, as experiments `dspy-uncompiled` and `dspy-compiled`.
- `OpikCallback`, installed once in `tracing.py`, which traces every DSPy call.

## See it in Opik

Open the **dspy-chess-openings-qa** project (local Opik at `http://localhost:5173`, workspace `default`).

- **Test suites tab.** One suite with 8 items. Open its two runs: `dspy-uncompiled` passed 0/8 and `dspy-compiled` passed 7/8 in the verified run. The uncompiled run is the interesting one. All eight fact assertions pass, while the card-tag and right-card assertions pass 0/8 and the "short answer" assertion passes 4/8. The model knew the chess and had never seen the convention.
- **Traces tab.** 22 traces from one run: 16 `evaluation_task` traces (8 per suite run), 5 `ChainOfThought` traces and 1 `ask_coach` trace. Open an `evaluation_task` trace: its `task` span contains `ask_coach`, then `ChainOfThought`, then `Predict`, then an `LM: openai - gpt-4o-mini` llm span with token usage and cost. Click that LM span in a compiled-run trace to see four worked examples sitting in the prompt, each with reasoning and a `| card:` answer. The same span in an uncompiled trace has none.
- **The 5 `ChainOfThought` traces** are the bootstrap teacher attempts from compiling; four passed the metric and became the demos. The `ask_coach` trace is the single question printed at the start.
- **Trace metadata.** `_opik_graph_definition` holds a mermaid diagram of the module graph (from `log_graph=True`).

A run costs about two cents and takes under a minute. The judge is an LLM, so the compiled pass count moves between runs (we saw 4 to 7 of 8 across builds, mostly on the card-tag assertion); the uncompiled run stayed at 0.

## Run it yourself

1. `cd dspy-chess-openings-qa`
2. `cp .env.example .env` and set `OPENAI_API_KEY` (a `.env` in a parent folder also works).
3. Start Opik locally and point the SDK at it (`opik configure --use_local`), or configure Opik Cloud.
4. `uv sync`
5. `uv run python main.py`
6. Open the printed run link, then the project's Traces tab.

Tests need no keys or Opik: `OPIK_TRACK_DISABLE=true uv run pytest`.

## Poke around

- Set `max_bootstrapped_demos=1` in `compiling.py` and recompile. How many of the three format assertions does one demo fix?
- Remove the `card` check from `house_format_metric`. Does the optimizer still pick demos that cite the right card?
- Add a question the cards cannot answer plus an assertion that the program says so. Neither the signature nor the demos cover refusals, so the suite will say whether that convention needs examples too.
- Compare an uncompiled and a compiled `LM` span input side by side; the prompt grows by the four demos.

## Gotchas we hit

**The suite has 16 items after you reworded some assertions.** `suite.insert(...)` skips items identical to stored ones, so an item with edited assertion text is treated as new and the old copy stays. Delete the suite's dataset (`client.rest_client.datasets.delete_dataset_by_name(dataset_name="dspy-chess-openings-qa")`) or its stale items before re-running.

**`AdapterParseError: Expected to find output fields in the LM response: [plan, answer]` in unit tests with `DummyLM`.** DSPy 3.5 names ChainOfThought's thinking field `plan` for a stub model that isn't a known reasoning model, and `reasoning` otherwise. Reply with both keys: `DummyLM([{"plan": "...", "reasoning": "...", "answer": "..."}])`, and pass `adapter=dspy.ChatAdapter()` to `dspy.context`.

## How it's put together

- `main.py` runs the demo question, the uncompiled suite run, the compile, the compiled suite run, then prints both pass rates and flushes.
- `chess_qa/handbook.py` holds the eight fictional opening cards.
- `chess_qa/examples.py` holds the eight worked tickets and the eight held-out test rows.
- `chess_qa/metric.py` holds the regex-and-fact check used to compile.
- `chess_qa/program.py` holds the signature, the program and the tracked `ask` helper.
- `chess_qa/compiling.py` configures `BootstrapFewShot`.
- `chess_qa/tracing.py` installs `OpikCallback` and sets the project name.
- `chess_qa/suite.py` builds the Opik test suite and runs it as an experiment.
- `tests/test_metric.py` covers the metric and checks the data splits don't overlap.
- `tests/test_program.py` runs the program and the suite task against a stub model, with tracking disabled.

*built with Opik · inspired by Opik's examples and documentation*
