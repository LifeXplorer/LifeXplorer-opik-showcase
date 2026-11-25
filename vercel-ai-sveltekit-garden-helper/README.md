# vercel-ai-sveltekit-garden-helper

**A streaming garden chat on SvelteKit, where every reply becomes an Opik trace, every conversation a thread, and an online rule grades each answer.**

![TypeScript](https://img.shields.io/badge/typescript-6-3178C6?style=flat&logo=typescript&logoColor=white)
![SvelteKit](https://img.shields.io/badge/sveltekit-3-FF3E00?style=flat&logo=svelte&logoColor=white)
![Vercel AI SDK](https://img.shields.io/badge/ai%20sdk-7-000000?style=flat&logo=vercel&logoColor=white)
![opik-vercel](https://img.shields.io/badge/opik--vercel-2.3.4-2f54eb?style=flat)

## The problem

A chat that streams has no single moment where your code holds "the answer". Tokens leave the server as they are produced, the browser re-sends the whole history on every turn, and a conversation is many requests that nothing links together. Logging by hand means stitching text deltas, guessing which requests belong to one person, and still not knowing whether the replies were any good.

This example is Sprout, a gardening assistant for the fictional Hollyhock Lane Community Garden. It answers planting questions over a streamed SvelteKit endpoint and can call a small `plantingCalendar` tool. The Vercel AI SDK emits OpenTelemetry spans, `opik-vercel` ships them to Opik, and a rule stored in Opik grades each reply as it arrives.

## What you'll build

- A SvelteKit page (`src/routes/+page.svelte`) using the `Chat` class from `@ai-sdk/svelte`, and one endpoint, `POST /api/chat`, that runs `streamText` on `gpt-4o-mini`.
- A `plantingCalendar` tool that reads `data/plants.json` (twelve crops, one made-up last-frost date of 4 May) and returns sow, plant-out and first-harvest dates.
- `src/instrumentation.server.ts`, the file SvelteKit runs once at server start. It starts an OpenTelemetry `NodeSDK` with `OpikExporter` and registers the AI SDK's telemetry integration. This file is the whole Opik integration.
- `scripts/opik-rule.ts`, which creates an LLM-as-judge online evaluation rule on the project through Opik's REST API.
- `scripts/demo.ts`, which creates the rule, starts the dev server, plays three two-turn conversations (tomatoes, aphids on kale, and a detour into mortgage rates), and stops the server.

```
browser Chat -> POST /api/chat -> streamText(gpt-4o-mini) -> tokens stream back
                                       |
                                       +-> OTel spans -> OpikExporter -> Opik project
                                                                          |
                                         online rule (judge) <-- new traces
```

## See it in Opik

Run the demo, then open `http://localhost:5173`, workspace `default`, and the project `vercel-ai-sveltekit-garden-helper`.

**Traces.** The table holds six traces named `garden-chat-turn`, one per streamed reply, each with a token count and a cost (about $0.00005 to $0.00012 per turn). It also holds six more, named `online_evaluation`: those are the judge's own calls, covered below. Open the first tomato turn. Its tree has two `llm` spans (`chat gpt-4o-mini`, 216 and 331 tokens, priced individually), a `tool` span `execute_tool plantingCalendar` between them, and a `general` span for each of the two agent steps. The model decided to call the tool, got dates back, and then streamed its answer. The turns that need no tool have just one `llm` span. The trace's input shows the whole message array, system prompt included, which is why input tokens grow as a conversation does.

**Threads.** Open the Threads tab and you will see three threads of four messages each, one per conversation. The browser's chat id travels with each request, and `src/lib/telemetry.ts` turns it into the thread id, so the two turns of "Tomatoes from seed" read as one transcript instead of two unrelated requests.

**Feedback scores.** Each `garden-chat-turn` trace has an `answered` feedback score, written by the rule `answered_the_garden_question` (listed among the project's online evaluation rules). In the verified run five turns scored 1. The sixth, the first banking question ("Can you recommend a good fixed mortgage rate..."), scored 0 with the judge's reason: it did not answer the question and redirected to gardening. Sprout behaved exactly as its prompt asks, and the score still flags the turn as not answered, which is the signal you want if you watch for users drifting out of scope. The next turn in that thread, about garlic, scored 1.

The rule lives on the project, not in your code, and it scores only traces that arrive after it exists. The demo therefore creates it before sending any traffic.

## Run it yourself

You need Node 24, an OpenAI key, and an Opik instance. The steps below assume a local Opik at `http://localhost:5173` with the OpenAI provider key stored in Opik's provider settings (the judge runs server-side and needs it).

1. `cp .env.example .env` and set `OPENAI_API_KEY` (a `.env` one folder up also works). Adjust the `OPIK_*` values if your Opik is not local.
2. `npm install`
3. `npm run demo`. It takes about 30 seconds and costs a fraction of a cent.
4. Wait a minute for the judge, then `npm run verify` to read the project back, or open it in the Opik UI.
5. To chat yourself: `npm run dev`, open `http://localhost:5173` (or the port Vite prints) and ask Sprout something. Each browser tab is its own thread.

Offline tests need no keys and no Opik: `OPIK_TRACK_DISABLE=true npm test`. `OPIK_TRACK_DISABLE=true` is the TypeScript SDK's switch for turning tracking off.

## Poke around

- Ask for a crop that is not in `data/plants.json`. The tool returns the list of known plants; compare the tool span's output with the reply.
- Edit the system prompt in `src/lib/garden.ts` so Sprout answers off-topic questions anyway, rerun the demo, and watch how the `answered` score for the mortgage turn changes.
- Change `sampling_rate` in `scripts/opik-rule.ts` to 0.5, delete the rule in the UI, rerun, and see how many traces get scored.
- Swap `gpt-4o-mini` in `src/routes/api/chat/+server.ts` for another model and compare the cost column.

## Gotchas we hit

**`npm install` fails with `ERESOLVE ... peer opik@"^1.8.75" from opik-vercel@2.3.4`.** `opik-vercel` declares a peer dependency on `opik` 1.x, but current `opik` is 2.x. Tell npm the peer is satisfied:

```json
"overrides": { "opik-vercel": { "opik": "$opik" } }
```

The same install can also stop on `peer @opentelemetry/api@">=1.10.0 <1.11.0" from @opentelemetry/sdk-node@0.301.2`, because `opik-vercel`'s `@opentelemetry/core` needs an API below 1.10. Pin `@opentelemetry/sdk-node` to `0.223.2` and `@opentelemetry/api` to `1.9.1`, as `package.json` does.

**The server runs and the chat works, but the project has no traces.** In AI SDK v7 the call only emits OpenTelemetry spans once an integration is registered. Starting the `NodeSDK` is not enough. Add it next to the exporter:

```ts
import { registerTelemetry } from "ai";
import { OpenTelemetry } from "@ai-sdk/otel";
registerTelemetry(new OpenTelemetry({ usage: true, enrichSpan }));
```

With the registration removed, the demo exited 0 and Opik held 0 traces.

**Traces are named `invoke_agent gpt-4o-mini` and the Threads tab is empty.** `enrichSpan` only receives the runtime context if the call opts in. Without it `runtimeContext` is `undefined`, so no thread id or trace name reaches the span. Opt in per call:

```ts
telemetry: { isEnabled: true, includeRuntimeContext: { threadId: true, traceName: true } }
```

**The project shows 12 traces for 6 chat turns.** The online rule's judge calls are logged in the same project as `online_evaluation` traces (an `llm` span and a `general` span each). They are not a bug and they are not scored themselves. Filter them out with `name != online_evaluation` when counting, as `npm run verify` does.

**`svelte.config.js is no longer used` and `Cannot find module '$lib/...'`.** SvelteKit 3 reads its config from the `sveltekit()` plugin in `vite.config.ts`, and the `$lib` alias is gone. Pass `sveltekit({ adapter: adapter() })` and import with relative paths.

## How it's put together

- `src/routes/+page.svelte` is the chat UI, built on the `Chat` class from `@ai-sdk/svelte`.
- `src/routes/api/chat/+server.ts` is the streaming endpoint, which hands the request to `streamGardenReply`.
- `src/lib/chat.ts` holds the `streamText` call: model, system prompt, tool, step limit, and the telemetry settings.
- `src/lib/garden.ts` has the system prompt, the planting date math, and the `plantingCalendar` tool.
- `src/lib/telemetry.ts` has the project name, the thread and trace-name mapping, and the per-request telemetry settings.
- `src/instrumentation.server.ts` is the Opik wiring: `NodeSDK`, `OpikExporter` and `registerTelemetry`.
- `src/lib/server-env.ts` loads `.env` from this folder and the one above it.
- `data/plants.json` is the fictional garden's crop table.
- `scripts/opik-rule.ts` creates the online evaluation rule idempotently.
- `scripts/demo.ts` runs the rule setup and the scripted conversations against a temporary dev server.
- `scripts/verify.ts` reads traces, spans, threads and scores back from Opik.
- `tests/garden.test.ts` covers the date math, plural handling, unknown crops and the tool.
- `tests/telemetry.test.ts` covers the span attribute mapping and the rule payload.
- `tests/chat.test.ts` streams a fake model through `streamGardenReply` with tracking disabled.
- `vitest.config.ts` keeps the tests independent of the SvelteKit plugin; the `pretest` script runs `svelte-kit sync` so the generated `.svelte-kit/tsconfig.json` that `tsconfig.json` extends exists on a fresh clone.

---

*built with Opik · inspired by Opik's examples and documentation*
