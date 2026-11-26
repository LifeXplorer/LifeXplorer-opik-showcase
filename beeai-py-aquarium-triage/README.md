# beeai-py-aquarium-triage

![Python](https://img.shields.io/badge/python-3.12%2B-3776ab?style=flat&logo=python&logoColor=white)
![BeeAI](https://img.shields.io/badge/beeai--framework-0.1.86-f5c518?style=flat)
![OpenInference](https://img.shields.io/badge/OpenInference-beeai%200.1.39-6f42c1?style=flat)
![Opik](https://img.shields.io/badge/Opik-OTLP%20ingestion-2f54eb?style=flat)

**A water-quality alert comes in at 3 a.m.; a BeeAI ReAct agent decides how worried to be, and Opik shows how it got there.**

## The problem

A fish room full of tanks produces alerts all day: ammonia up here, pH drifting there. A ReAct agent can triage them,
but it reasons in a loop (think, call a tool, think again), and `agent.run()` hands you back only the last line.
When it calls a pH reading "urgent" you want to know whether it fetched the right tank, read the right threshold,
or just guessed. This example triages alerts for the fictional Brightwater Aquatics fish room and sends the whole loop to Opik
through OpenInference and plain OpenTelemetry, with no Opik SDK in the app code.

## What you'll build

One `ReActAgent` on `gpt-4o-mini` with two read-only tools over small JSON files in `data/`:
`lookup_tank` (type, inhabitants, keeper) and `lookup_safe_range` (safe band and urgent thresholds per tank type).
`uv run main.py` triages three scripted alerts:

| Alert | Expected |
|---|---|
| reef-01 ammonia 0.25 ppm (reef ammonia should be 0, urgent above 0.1) | urgent |
| shrimp-04 pH 7.6 (safe 6.2-7.4, urgent above 7.9) | watch |
| comm-07 temperature 26.5 C (safe 22-27) | ok |

All of the Opik wiring sits in `tracing.py`: BeeAI's `BeeAIInstrumentor`, an OTLP exporter aimed at Opik, and a small
exporter subclass that cleans the spans up for Opik (see Gotchas).

## See it in Opik

Open the **beeai-py-aquarium-triage** project (workspace `default`, `http://localhost:5173`). The Traces tab has
**3 traces**, one per alert, each named `ReAct`. In the verified run each trace held 6 spans, 18 in total:
1 `ReAct` span (type `general`) as the root, 3 `OpenAIChatModel` spans (type `llm`), and 2 tool spans (type `tool`),
`lookup_tank` then `lookup_safe_range`, all direct children of the root.

- Click a `lookup_tank` span: the input holds `{"tank_id": "reef-01"}`-style arguments and the output is the tank JSON the model read next.
- Click an `OpenAIChatModel` span: model `gpt-4o-mini`, provider `openai`, prompt/completion token usage (including
  cached prompt tokens on later turns) and an estimated cost of roughly $0.00014-0.0002 per span.
- Click the `ReAct` root: its metadata lists every iteration (`iterations.1.thought`, `.tool_name`, `.tool_input`,
  `.tool_output`, ... up to `iterations.3.final_answer`). The framework's "iteration" lives here as metadata, not as separate spans.
- The traces list shows per-trace cost: about $0.0004-0.0005 for each alert, about $0.0013 for the run (wall time 22-26 s).

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and have a running Opik (self-hosted at `http://localhost:5173`, or Opik Cloud).
2. `cp .env.example .env` and set `OPENAI_API_KEY` (a repo-root `.env` is also found).
3. Self-hosted: nothing else. For Opik Cloud set `OPIK_URL_OVERRIDE=https://www.comet.com/opik/api/`, and add an
   `Authorization` header in `tracing.py` with your key (never commit it).
4. `uv run --python 3.12 main.py`
5. Open the project above and click the newest trace.
6. Offline tests: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- In `data/water_ranges.json` lower the shrimp `ph` `urgent_above` to 7.5 and rerun: alert 2 should flip from `watch` to `urgent`, and the `lookup_safe_range` output shows why.
- Add a fourth alert with an unknown tank id (`reef-99`). The `lookup_tank` span returns the error JSON with `valid_ids`; see how the agent recovers.
- Pass `max_iterations=2` in `triage.py`: the agent is cut off before it can read the second tool result, and the root span's iteration metadata stops early.
- Remove the `new_token` filter in `tracing.py` and compare the span count per trace.

## Gotchas we hit

**Symptom: `TypeError` / unexpected keyword when following the BeeAI docs for `agent.run`.** The Python API in
beeai-framework 0.1.86 no longer takes `execution=AgentExecutionConfig(...)`. Pass the limits as keyword arguments:
`await agent.run(prompt, max_iterations=8, max_retries_per_step=3, total_max_retries=6)`.

**Symptom: every trace holds hundreds of `new_token` spans, and the exporter logs `Failed to export spans batch`.**
BeeAI streams the model and the instrumentation emits one span per streamed chunk. Drop them before export:
`kept = [s for s in spans if s.name != "new_token"]` in `OpikFriendlyExporter.export`.

**Symptom: llm spans show cost = null (and an empty provider).** OpenInference writes `llm.provider` and its own
`llm.cost.*`, but Opik prices a span from `gen_ai.provider.name` + model + usage. Copy it over:
`attrs["gen_ai.provider.name"] = attrs["llm.provider"]`.

**Symptom: tool calls appear as type `general` instead of `tool`.** Opik types a span `tool` only from
`gen_ai.tool.call.arguments` / `gen_ai.tool.call.result`. Re-publish OpenInference's `input.value` / `output.value`
under those keys for `TOOL` spans (see `opik_attributes`).

**Symptom: an `OpenAIChatModel` span with 0 tokens and no cost.** In this version the instrumentation sometimes
records a model call with no usage (2 of the 9 llm spans in the verified run). It is a gap in the reported usage,
not a free call: that turn's tokens are missing from the trace total.

## How it's put together

- `main.py`: loads env, switches tracing on, runs the three alerts, flushes at exit.
- `triage.py`: the prompt, `ReActAgent` setup, and the parser for the `Severity/Why/Action/Notify` answer.
- `tools.py`: the two tools and the plain functions behind them.
- `tracing.py`: OpenInference instrumentation, OTLP exporter to Opik, span clean-up.
- `data/tanks.json`, `data/water_ranges.json`: the fictional fish room.
- `tests/test_triage.py`: offline tests for the parser, tools, prompt, span rewrite, and an agent run with a stubbed agent and tracking disabled.

---
*built with Opik · inspired by Opik's examples and documentation*
