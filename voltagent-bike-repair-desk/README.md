# voltagent-bike-repair-desk

*A VoltAgent bike-shop assistant whose tokens and costs only show up in Opik once its OpenTelemetry attributes are renamed.*

![Node](https://img.shields.io/badge/node-20.19%2B-339933?style=flat&logo=node.js&logoColor=white)
![VoltAgent](https://img.shields.io/badge/%40voltagent%2Fcore-2.11-1b1f23?style=flat)
![Opik](https://img.shields.io/badge/Opik-OTLP%20ingestion-2f54eb?style=flat)

## The problem

VoltAgent traces itself with OpenTelemetry, and Opik accepts OTLP, so wiring the two together takes a dozen lines. The catch is what arrives. VoltAgent labels its spans with its own vocabulary (`llm.usage.prompt_tokens`, `llm.model`, `span.type`), while Opik's OTel ingestion looks for the GenAI semantic conventions (`gen_ai.request.model`, `gen_ai.usage.*`, `gen_ai.provider.name`). Send the spans unchanged and the traces arrive, every span is a plain `general` span, and there is no token count and no cost anywhere. This example is a small bike-shop assistant that makes that gap visible, then closes it with a 60-line exporter wrapper.

## What you'll build

A front-desk assistant for a fictional shop, Cog & Crank Cycle Works, running on `gpt-4o-mini` with three tools over in-memory data:

- `repair_status` looks up a ticket (`RT-2043`, `RT-2051`, `RT-2058`) and returns its state and pickup estimate.
- `find_parts` searches the parts shelf by keyword and bike type, with price and stock.
- `quote_repair` prices part SKUs plus flat-rate labor jobs and adds 8% tax.

`npm run demo` sends three customer messages: a status check, a "what would a new chain and rear tire cost me" request that makes the agent chain `find_parts` and `quote_repair`, and a ticket that is stuck on a sold-out tire. `npm run verify` then reads the Opik project back over REST and checks that the mapping delivered.

## See it in Opik

Open the **voltagent-bike-repair-desk** project (local: <http://localhost:5173>, workspace `default`). After one demo run it holds **3 traces** and **13 spans** (3 root, 3 llm, 7 tool; the tool count can vary by a call or two between runs): per trace one root span named `cog-and-crank-front-desk` (type `general`), its `llm:generateText` child steps (type `llm`) and the `tool.execution:*` children (type `tool`).

- Click an `llm:generateText` span. Model `gpt-4o-mini`, provider `openai`, token usage (in our run 639 prompt + 87 completion = 726 total) and an estimated cost of about $0.00015. The Traces table's usage and cost columns are filled too. One caveat: VoltAgent reports the usage of the final model step on this span, while the root span's own `usage.*` attributes (kept as metadata) cover every step, so on multi-tool requests the cost shown is a lower bound.
- Click a `tool.execution:quote_repair` span. Its input holds the exact arguments the model chose, such as `part_skus: ["CH-108", "TR-701"]` and `labor_jobs: ["chain-replace", "tire-swap"]`, and its output holds the quote the shop returned. That is where you notice when the model forgot a labor line while the chat reply sounds confident.
- Open the root span: the customer message is the trace input, the assistant's reply the output.
- For the "before" picture, run `OPIK_RAW_ATTRS=true npm run demo` (see below). In our run that produced 3 traces and 13 spans, **all** of type `general`, with no usage and no cost.

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY` (the repo-root `.env` is also picked up). Start a local Opik, or point the `OPIK_*` variables at Opik Cloud.
2. `npm install`
3. `npm run demo` (about 15 seconds, well under a cent of `gpt-4o-mini`).
4. `npm run verify` to see the audit: counts, one line per llm and tool span, and PASS/FAIL checks.
5. Offline tests, no keys needed: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true npm test`.

## Poke around

- Run `OPIK_RAW_ATTRS=true npm run demo`, then `npm run verify`: the checks fail one by one. Delete those traces before the mapped run so the counts stay readable.
- In `src/genai.ts`, drop the `gen_ai.provider.name` line and re-run. Tokens still land, but `total_estimated_cost` is null, because Opik prices a span only when it recognizes the provider.
- Ask for a part that is sold out (the Marathon tire, `TR-700`) and read the `find_parts` output next to what the assistant told the customer.
- Remove `gen_ai.agent.` from the leftover loop in `toGenAI` and look at a tool span's input: every attribute Opik has no rule for lands there.

## Gotchas we hit

**Every span is `general`, and usage and cost are empty.** VoltAgent's own attribute names are not recognized by Opik's OTel mapper. Rename them in an exporter wrapper (`src/genai.ts`) and wrap the OTLP exporter with it: `new GenAIExporter(opikExporter(), "openai")`.

**Cost is null even though tokens are present.** Opik computes `total_estimated_cost` only for a recognized provider. VoltAgent puts the provider on the agent span (`ai.model.provider`) but not on the llm span, so set `gen_ai.provider.name` yourself.

**The tool span's input is a wall of `entity.id`, `operation.id`, `tool.call.id`.** Opik files every attribute it has no mapping rule for into the span input. Rename the leftovers to `gen_ai.agent.<name>`, which Opik stores as metadata, and drop the bulky duplicates (`tool.parameters`, `agent.messages.ui`, `agent.stateSnapshot`).

**`npm install` fails with an ERESOLVE on the OTLP exporter.** The newest exporter (0.301) wants `@opentelemetry/api` 1.10 and its own SDK, which VoltAgent's pinned OTel 2.0 packages do not satisfy. This example pins `@opentelemetry/exporter-trace-otlp-proto@^0.205.0`.

## How it's put together

- `src/shop.ts`: tickets, parts shelf, labor rates, and the pure functions behind the tools (lookup, search, quote with tax).
- `src/tools.ts`: the three VoltAgent tools, thin wrappers over `shop.ts`.
- `src/agent.ts`: the front-desk agent (model, instructions, temperature 0).
- `src/genai.ts`: `toGenAI`, the attribute rename, and `GenAIExporter`, the exporter wrapper that applies it.
- `src/observability.ts`: the OTLP exporter aimed at Opik, the `OPIK_TRACK_DISABLE` and `OPIK_RAW_ATTRS` switches; the only file that wires tracing in.
- `src/env.ts`: loads `.env` and clears any proxy base URL.
- `src/demo.ts`: three scripted requests, then flushes the exporter.
- `src/verify.ts`: reads the project back over REST and prints PASS/FAIL checks.
- `tests/shop.test.ts`: quote math, part filtering, ticket lookup.
- `tests/genai.test.ts`: the llm, tool and agent-span renames, and the exporter wrapper.
- `tests/tracing-disabled.test.ts`: with `OPIK_TRACK_DISABLE=true` there are no span processors and tools still run.

---

*built with Opik · inspired by Opik's examples and documentation*
