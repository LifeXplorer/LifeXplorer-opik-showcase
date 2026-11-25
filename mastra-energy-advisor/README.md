# Wattle: a home-energy advisor you can watch think

**`mastra-energy-advisor`** · an agent that reads a smart meter, prices tariffs and sizes up appliances, with every tool call recorded in Opik.

![Node](https://img.shields.io/badge/node-22.13%2B-339933?style=flat&logo=node.js&logoColor=white)
![Mastra](https://img.shields.io/badge/%40mastra%2Fcore-1.86-0b0b0b?style=flat)
![Opik](https://img.shields.io/badge/Opik-OTLP%20ingestion-2f54eb?style=flat)
![Tests](https://img.shields.io/badge/tests-vitest-6e9f18?style=flat)

Ask an energy advisor "should we switch tariff?" and you get a confident dollar figure. Was it computed from the real meter data, or did the model improvise? Did it price both plans, or only the one it liked? The chat text can't tell you. Wattle is a small [Mastra](https://mastra.ai/) agent for a fictional household (Willow Lane 14) that answers by calling tools, and Opik's trace tree shows every call it made, with the arguments it chose and the numbers it got back.

## What you'll build

- One Mastra `Agent` on `gpt-4o-mini`, instructed to never quote a number it did not get from a tool.
- Three tools over canned data in `src/data/home.ts`: `read_meter` (a week of peak and off-peak kWh), `compare_tariffs` (prices that week on a flat plan or a time-of-use plan), and `estimate_appliance` (daily kWh and cost of a dryer, dishwasher, EV charger and so on).
- The arithmetic in `src/energy.ts`, kept free of Mastra so it can be unit tested.
- Tracing as configuration: `src/observability.ts` builds Mastra's `Observability` with an `OtelExporter` aimed at Opik. Agent and tool files contain no tracing code.

`npm run demo` asks three questions. The third makes the agent chain tools to price an EV charger on peak and off-peak rates.

## See it in Opik

Open the **`mastra-energy-advisor`** project. The traces table has three rows, one per question, all named `invoke_agent wattle-energy-advisor`. In the demo run they held 18, 22 and 15 spans, and cost between $0.0002 and $0.0003 each.

Click the second row (the tariff comparison). The tree reads `invoke_agent` > `agent_step` > `chat gpt-4o-mini` plus, beside it, the `execute_tool` span for whatever the model decided to call. Here you will find two `execute_tool compareTariffs` spans with type **tool**: one with `tariff_id: "flat-saver"` returning $34.14 for the week, one with `"evening-shift"` returning $32.95. Those two spans are the receipt for the answer "you'd save about $1.19 a week". Question 1 has a single `execute_tool readMeter` span with `days: 7`; question 3 has two `execute_tool estimateAppliance` spans, one with `run_at_peak: true` ($4.30 a day) and one with `false` ($1.79 a day).

Each `chat` span is typed **llm** and carries model `gpt-4o-mini`, prompt and completion tokens, and an estimated cost, which rolls up to the trace (for example 1,513 prompt tokens and 131 completion tokens for question 2). Mastra also emits `processor_run`, `model_generation` and `model_chunk` spans as plain **general** spans; collapse them if they are noise.

Two limits to know about: the trace-level **Output** column is empty (Mastra's OTel mapping puts the whole run, final answer included, under `mastra.agent_run.output` inside the span's **Input** attributes, so read it there or in your terminal), and tool spans are named after the key in the agent's `tools` object (`compareTariffs`), not the tool `id` (`compare_tariffs`).

## Run it yourself

1. `cd mastra-energy-advisor && npm install`
2. Put `OPENAI_API_KEY` in a `.env` here (see `.env.example`) or in a parent folder's `.env`.
3. Tell it where Opik is. For Opik Cloud: `OPIK_API_KEY` and `OPIK_WORKSPACE_NAME`. For a local Opik: `export OPIK_URL_OVERRIDE=http://localhost:5173/api/ OPIK_WORKSPACE=default` (no key needed).
4. `npm run demo`: about 15 seconds and well under a cent.
5. Open the `mastra-energy-advisor` project in Opik. Change the project with `OPIK_PROJECT_NAME`.

Offline checks: `OPIK_TRACK_DISABLE=true npm test` runs vitest with no keys and no exporter (that variable is this example's own switch, read in `src/observability.ts`), and `npm run typecheck` runs `tsc`.

## Poke around

- Make the household cheaper on the flat plan: raise `evening-shift`'s `peakRate` in `src/data/home.ts` to 0.60, rerun, and compare the two `compareTariffs` spans in question 2.
- Ask something the tools cannot answer ("what's the carbon intensity of our grid?") and see whether the trace shows the agent calling a tool at all, or answering from thin air.
- Set `maxSteps: 1` in `src/run.ts`: the loop stops after the first model call and the trace shrinks accordingly.
- Remove the "never guess numbers" sentence from the instructions in `src/agents/advisor.ts` and see whether `readMeter` is still called before the usage answer.

## Gotchas we hit

**Nothing shows up in Opik and the run exits 0.** With `protocol: "http/json"` the local Opik rejects the export with `Bad Request`, and Mastra only logs that when the exporter is in debug mode. Use protobuf (`npm i @opentelemetry/exporter-trace-otlp-proto`) and `protocol: "http/protobuf"` in `OtelExporter`'s `custom` provider. Run with `OTEL_DEBUG=1 npm run demo` to see `Export completed: N spans sent successfully`.

**Last spans missing after the script ends.** The exporter batches every 5 seconds. Call `await mastra.shutdown()` before exit, as `src/run.ts` does, to flush.

**Trace Output column is empty.** The trace shows `output: null` after a successful run. The exporter stores the final text in the input attributes (`mastra.agent_run.output`) instead, so nothing is broken; read it there.

## How it's put together

- `src/data/home.ts`: the fictional meter readings, two tariffs and five appliances.
- `src/energy.ts`: summing readings, pricing a tariff, appliance energy and cost.
- `src/tools/`: the three Mastra tools (`meter.ts`, `tariff.ts`, `appliance.ts`) and an index.
- `src/agents/advisor.ts`: Wattle's instructions, model and tool list.
- `src/observability.ts`: the Opik OTLP exporter and its headers, the only Opik code.
- `src/mastra.ts`: the Mastra instance that registers the agent and the observability config.
- `src/questions.ts`, `src/run.ts`: the three scripted questions and the runner that flushes at the end.
- `tests/energy.test.ts`, `tests/tools.test.ts`: offline tests of the maths, the tools, and the tracing switch.

---

*built with Opik · inspired by Opik's examples and documentation*
