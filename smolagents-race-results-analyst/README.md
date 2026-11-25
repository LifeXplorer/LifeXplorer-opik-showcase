# smolagents-race-results-analyst

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![smolagents](https://img.shields.io/badge/smolagents-1.26-FFD21E?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.3.4-2f54eb?style=flat)

*A marathon-results analyst that answers by writing pandas, and a trace that lets you read the pandas it wrote.*

Ask a code-writing agent "which club runs the best negative splits?" and you get a sentence with a
percentage in it. Nothing in that sentence tells you whether the percentage came from the right
comparison. This example makes the problem concrete: one of its three questions is answered
confidently and wrongly on every run, and the only place the mistake is visible is in the code the
model generated. Opik is where you read that code.

## What you'll build

A smolagents `CodeAgent` on `gpt-4o-mini` with a single capability: running Python with `pandas`
available. It reads `data/saltmarsh_2025.csv`, 240 fictional starters in the Saltmarsh Coastal
Marathon (bib, runner, gender, age group, club, half-way split, chip time as `H:MM:SS` text, and a
FIN/DNF status). The file has three planted facts:

- one clear winner in the women's 40-44 group (Odile Fenwick, 3:04:18),
- one club, Dune Pacers, where two thirds of finishers ran a negative split (other clubs sit at 8-14%),
- one age group, 60+, with a DNF rate of 23.5% (the others are 0-6%).

`analysis.py` recomputes all three with the standard library, no pandas and no model, so every
answer can be graded. After the three questions run, `main.py` writes the verdict back onto each
Opik trace as a `matches_ground_truth` feedback score. Tracing is OpenInference's
`SmolagentsInstrumentor` exporting over OTLP to Opik; there are no decorators in the agent code.

## See it in Opik

Open the `smolagents-race-results-analyst` project (local Opik: http://localhost:5173, workspace
`default`). You get three traces, one per question, each rooted at `CodeAgent.run`, and a
`matches_ground_truth` column in the traces table: 1.0 for the winner question, 0.0 for the club
question, 1.0 for the DNF question.

Open the 0.0 trace (the "highest percentage of finishers who ran a negative split" one). It has
8 spans: the `CodeAgent.run` root, three `OpenAIModel.generate` calls, three `Step` spans and a
`FinalAnswerTool` call. Two kinds of span carry the evidence:

- **`OpenAIModel.generate`** (type `llm`): its output is the model's `Thought:` followed by the
  `<code>` block it wants to run. In the verified run you can read
  `finishers['half_split'] < (finishers['chip_time'] / 2)`. That says "first half shorter than
  half the total", which is a *positive* split; a negative split is the opposite. The code is
  tidy, runs cleanly and answers a different question than the one asked.
- **`Step 1`, `Step 2`, ...** (type `general`): the output is the execution log, the text the
  local executor captured. In that run `Step 1` is marked as failed: its error is
  `Code parsing failed on line 33 ... SyntaxError: unterminated string literal` (the model typed
  `print(fClub ...`), and `Step 2` is the retry. Its log reads "Club with highest percentage:
  Harbour Striders, Percentage: 92.3%". That is the
  share of runners who went out *faster* than they came home, which is why a club of ordinary
  runners looks "best" and Dune Pacers (66.7% real negative splits) is never mentioned.

The other two traces show what a healthy run looks like: each finishes in two steps, and the
generated code and the `Step` log agree with the grader. Which question goes wrong is stable, but
the surrounding detail is not: across the runs made while building this, the club question was
wrong every time, once with "No clubs have finishers with a negative split", and a syntax-error
retry like the one above showed up only in some runs.

Each `OpenAIModel.generate` span carries `gpt-4o-mini` as its model, `openai` as its provider, its
own token counts and a cost. In the club trace the three calls used 2,707, 4,277 and 3,700 tokens
and cost $0.00065, $0.00068 and $0.00076, so the trace shows $0.0021; the whole run costs about
$0.004.

## Run it yourself

1. Put `OPENAI_API_KEY` in a `.env` (copy `.env.example`), or in a `.env` one directory up.
2. Start Opik. This example expects a local instance at `http://localhost:5173`; for Opik Cloud set
   `OPIK_URL=https://www.comet.com/opik/api`, `OPIK_API_KEY` and `OPIK_WORKSPACE` in `.env`.
3. `uv sync`
4. `uv run main.py` (about 45 seconds and roughly $0.004 of `gpt-4o-mini`).
5. Open the project and compare the three traces as described above.
6. Offline tests, no keys and no Opik needed:
   `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

`OPIK_TRACK_DISABLE=true` turns the OTLP exporter off in `tracing.py` too, so the app itself runs
without exporting anything (it then skips the feedback step).

## Poke around

- Rephrase question 2 ("negative split" -> "ran the second half faster than the first") and see
  whether the generated comparison flips. The trace shows which wording the model actually coded.
- Add the missing column hint to `BRIEFING` ("negative split means `chip_time - half_split <
  half_split`") and re-run. Does the club answer become Dune Pacers?
- Remove `"pandas"` from `additional_authorized_imports` and run again; look at what the `Step`
  spans report when the generated code can no longer import its main tool.
- Plant your own finding in `data/saltmarsh_2025.csv` (for example make a second club negative-split)
  and add its expected answer to `expected_answers` in `analysis.py`.

## Gotchas we hit

**The model-call spans show `cost: null`.** OpenInference reports the model name (`gpt-4o-mini`) but
no provider, and Opik prices a span only when it has both. `tracing.py` adds a small span processor
that stamps `gen_ai.system="openai"` on the `*.generate` spans as they start; Opik reads that as the
span's provider and fills in the cost:

```python
class ProviderTagger(SpanProcessor):
    def on_start(self, span, parent_context=None):
        if span.name.endswith(".generate"):
            span.set_attribute("gen_ai.system", "openai")

provider.add_span_processor(ProviderTagger("openai"))  # before the exporter's processor
```

**The trace's token total is twice what the model calls add up to.** In the club trace the trace-level
usage says 21,368 total tokens while the three `OpenAIModel.generate` spans sum to 10,684.
OpenInference puts the accumulated token count on the `CodeAgent.run` agent span as well, and Opik
types that span `llm`, so it is counted again. Sum the per-call spans when you need the real number:

```python
calls = [s for s in client.search_spans(project_name=P, trace_id=t.id) if s.name == "OpenAIModel.generate"]
tokens = sum(s.usage["total"] for s in calls)
```

**`400 Invalid value '...+00:00' ... for field 'start_time'`** when filtering traces by time. A
timezone offset written as `+00:00` loses its `+` on the way and Opik rejects the date. Use a `Z`
suffix instead, as `feedback.py` does:
`started.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")`.

## How it's put together

- `main.py`: the briefing, the three questions, the `CodeAgent`, grading and the run loop.
- `tracing.py`: OTLP exporter, `SmolagentsInstrumentor` and the `ProviderTagger` that makes model calls priceable; routes traces to the project named in the `projectName` header.
- `feedback.py`: finds each question's trace and logs the `matches_ground_truth` score.
- `analysis.py`: stdlib ground truth and the `check_answer` grader.
- `data/saltmarsh_2025.csv`: 240 fictional runners; `data/generate_results.py` regenerates it from a fixed seed.
- `tests/test_analysis.py`: the planted facts, the DNF/small-club rules, the grader.
- `tests/test_agent.py`: the real `CodeAgent` on a stub model with tracing disabled, plus the provider tagger, trace-matching and score logic.

---

*built with Opik · inspired by Opik's examples and documentation*
