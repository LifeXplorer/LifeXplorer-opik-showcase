<div align="center">

# openai-ts-museum-guide

**A visitor-guide chatbot for a make-believe clock museum, traced so each conversation reads as one thread.**

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![Node](https://img.shields.io/badge/node-20%2B-339933?style=flat&logo=node.js&logoColor=white)
![openai](https://img.shields.io/badge/openai-6.x-412991?style=flat&logo=openai&logoColor=white)
![opik](https://img.shields.io/badge/opik%20%2B%20opik--openai-2.3.4-2f54eb?style=flat)

</div>

A guide that answers one question at a time is easy to log. A guide that holds a *conversation* is not: the visitor asks about the cuckoo clock, then "when do they come out?", and in a plain request log the second message is a stranger with no past. You cannot tell which visitor it belonged to, what that visit cost, or whether they left happy.

This example is the guide for The Wrenfield Museum of Clocks & Curiosities (fictional). It uses the OpenAI TypeScript SDK, `opik-openai`, a `threadId` per visitor, and a feedback score logged after the run. It makes three real API calls per conversation and costs a fraction of a cent.

## What you'll build

- `MuseumGuide`: one object per visitor that keeps message history and, on every turn, looks up the exhibits mentioned in the latest message and puts them in the system prompt.
- One Opik **trace per turn** named `guide-turn`, with `threadId` set to the conversation id and `metadata` holding the turn number and matched exhibit ids.
- `trackOpenAI` wrapped around the OpenAI client with the turn's trace as `parent`, so the completion lands as a child span with model, messages, token usage and cost.
- A `visitor-rating` feedback score attached, after the run, to the last turn of each scripted conversation.

The demo plays two conversations (a family planning a Saturday visit, and a wheelchair user asking about the tower) of three turns each, with no typing needed.

## See it in Opik

Open `http://localhost:5173` (or your Opik Cloud workspace) and pick the **`openai-ts-museum-guide`** project.

- **Logs tab.** Six rows, all named `guide-turn`. Each shows the visitor's message as input and the guide's reply as output. The `visitor-rating` column holds `1` on the third `family-visit` turn and `0` on the third `accessibility-question` turn; sort by it to pull low-rated turns to the top. Each row also has a cost in the order of $0.00006 to $0.00009 (for example 263 prompt tokens, about $0.00007, on the first turn).
- **Open a trace.** Inside is a single span, `guide-completion`, with provider `openai`, model `gpt-4o-mini-2024-07-18`, the full message array (system prompt with the matched exhibits, then every earlier turn) and token usage. Prompt tokens per turn were 263, 293, 364 for the family visit: the history grows, and the exhibit context changes with the question. The span type shows as `general`: that is how `opik-openai` logs it, and cost is still computed.
- **Threads tab.** Two threads, `family-visit-<random suffix>` and `accessibility-question-<random suffix>`, six messages each and a combined cost of about $0.00022 apiece. Open one to read it as a transcript. This is the view the six separate rows could not give you.
- **A thing worth reading.** In the `accessibility-question` thread the last answer says the orrery is "wound by hand". The exhibit text only says it is driven by a weight-and-chain movement and needs winding on Thursdays, so that detail is the model's guess, and the thread is where you notice it. (Model output varies between runs; the 0 rating is scripted, not a judgement of that run.)

## Run it yourself

1. `cp .env.example .env` and set `OPENAI_API_KEY`. A `.env` further up the tree is found too. For Opik Cloud add `OPIK_API_KEY` and remove the `OPIK_URL_OVERRIDE` line.
2. `npm install`
3. `npm run demo` (about 10 seconds; for your own conversation use `npm run dev`).
4. Open the `openai-ts-museum-guide` project in Opik as described above.
5. `npm test` runs the offline tests; no keys or server needed. `vitest.config.ts` sets `OPIK_TRACK_DISABLE=true`, Opik's switch for turning tracking off, so the traced guide runs in tests without sending anything (the project's trace count stays the same).

## Poke around

- Run `npm run dev`, chat with the guide, and watch a new `interactive-<suffix>` thread grow while you type.
- Ask about something the collection does not mention ("do you sell postcards?") and open the trace: the system prompt reads `no specific exhibit matched`, and the guide should send you to the front desk.
- In `src/demo.ts`, change a `value` in `RATINGS` and re-run; the `visitor-rating` column in Logs follows.
- Change `MODEL` in `src/guide.ts` to `gpt-4.1-mini` and compare the cost column.

## Gotchas we hit

### Re-running puts old and new turns in one thread

Symptom: after running the demo twice, the `family-visit` thread shows 12 messages instead of 6 and its cost doubles.
Cause: `threadId` was the bare label `family-visit`, and Opik groups every trace with the same id into one thread.
Fix: make the id unique per conversation, as `newThreadId` in `src/guide.ts` does:

```ts
export function newThreadId(label: string): string {
  return `${label}-${randomUUID().slice(0, 8)}`;
}
```

### `npm install opik opik-openai` fails with ERESOLVE

Symptom: `peer opik@"^1.8.61" from opik-openai@2.3.4` conflicts with `opik@2.3.4`.
Cause: `opik-openai` still declares a peer dependency on the 1.x SDK.
Fix: add an override to `package.json` that points it at your own `opik`:

```json
"overrides": { "opik-openai": { "opik": "$opik" } }
```

## How it's put together

- `src/guide.ts`: `MuseumGuide` (history, per-turn trace, `trackOpenAI` wrapper) and `newThreadId`.
- `src/collection.ts`: loads the collection, keyword lookup, system prompt builder.
- `src/feedback.ts`: `logVisitorRating`, which logs the `visitor-rating` score on a trace.
- `src/demo.ts`: scripted conversations, simulated ratings, interactive mode, final `flush()`.
- `src/env.ts`: loads the nearest `.env`.
- `data/collection.json`: the fictional museum: hours, tickets, six exhibits.
- `tests/`: collection lookup, the guide with a stubbed client and tracking disabled, and the feedback call.
- `vitest.config.ts`: turns tracking off for tests.

---

*built with Opik · inspired by Opik's examples and documentation*
