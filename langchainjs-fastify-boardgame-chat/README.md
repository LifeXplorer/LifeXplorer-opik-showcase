# langchainjs-fastify-boardgame-chat

*A board-game cafe chat widget whose conversations read like conversations in Opik.*

![Node](https://img.shields.io/badge/node-20%2B-339933?style=flat&logo=nodedotjs&logoColor=white)
![Fastify](https://img.shields.io/badge/fastify-5-000000?style=flat&logo=fastify&logoColor=white)
![opik-langchain](https://img.shields.io/badge/opik--langchain-2.3.4-2f54eb?style=flat)

## The problem

A chat widget talks to your server one `POST` at a time. A guest who asks three questions leaves three requests, and in a trace list they look like strangers. Opik's **Threads** tab can stitch them back into one conversation, but whether that thread reads like a chat or like a pile of JSON depends on one decision you make in your chain: what the root run takes in and hands back. This example shows both outcomes side by side.

## What you'll build

The server behind the chat widget of Meeple & Brew, a fictional board-game cafe. A guest says who is coming and what kind of evening they want; the host replies with one or two games.

- `POST /chat` runs a LangChain.js chain that takes the guest's message as a **string** and returns the reply as a **string**. Inside, it loads that guest's history, shortlists games from `data/games.json` (party size, time, difficulty, mood), then runs prompt, `gpt-4o-mini` and a string parser.
- `POST /chat-envelope` runs the same steps, but the root takes `{ message, sessionId }` and returns `{ reply, sessionId }`, which is how plenty of real backends wrap their chains.
- One `OpikCallbackHandler` per guest, with the widget's `sessionId` as its `threadId`, is the whole tracing setup.
- `npm run demo` plays two guests on `/chat` (three turns each) and one on `/chat-envelope` (two turns), then flushes.

## See it in Opik

Open the **`langchainjs-fastify-boardgame-chat`** project after a demo run. It holds 8 traces, one per turn, all named `cafe-widget-turn`.

**Threads tab.** Three threads: `guest-birthday-four` and `guest-date-night` with 6 messages each (3 guest turns, 3 replies), and `guest-envelope-variant` with 4. In the first two, each message is a single `value` holding the sentence the guest typed or the host answered ("It's the two of us tonight, something cozy.", then the recommendation). In `guest-envelope-variant` the messages are multi-field objects instead: `{"message":{"value":"Four of us, we like bluffing games..."},"sessionId":{...}}` and `{"reply":{"value":"..."},"sessionId":{...}}`. Same kind of guest, same model, but the transcript is structured data instead of sentences. The only difference is the chain's input and output shape.

**Trace tree.** Open any `cafe-widget-turn` trace: the root contains `prepare-turn` (history load plus shortlist), `ChatPromptTemplate`, `ChatOpenAI` and `StrOutputParser`. The `ChatOpenAI` span is the only `llm` span: it shows `gpt-4o-mini`, around 370 to 390 total tokens per turn, and a cost near $0.00007. Click it to see the exact system prompt, including the shortlist the host was allowed to pick from. The envelope traces add `unwrap-envelope` and `wrap-envelope` spans around the same steps.

## Run it yourself

1. `cp .env.example .env` and set `OPENAI_API_KEY`. For a local Opik leave the two `OPIK_*` lines; for Opik Cloud add `OPIK_API_KEY` and your workspace.
2. `npm install`
3. `npm run demo` (about a minute, well under one cent of tokens).
4. Open the `langchainjs-fastify-boardgame-chat` project in Opik and go to Threads.
5. To use the widget: `npm run dev`, then open http://localhost:3000. Each browser tab gets its own `sessionId`.
6. `npm test` runs the offline tests. `vitest.config.ts` sets `OPIK_TRACK_DISABLE=true` (the SDK's switch for turning tracing off) and blanks `OPENAI_API_KEY`, so no keys or Opik server are needed.

## Poke around

- Open the widget in two tabs and ask the same question. Two `sessionId`s, two threads, and the second host has no memory of the first.
- In `src/tracing.ts`, delete the `threadId: sessionId` line, rerun the demo (after clearing the project), and watch the Threads tab lose its conversations while the traces stay.
- Ask for something the catalog cannot seat ("a group of twelve") and read the `ChatPromptTemplate` span: the shortlist is empty and the host should say so.
- Edit `data/games.json`, add a game with a tag the parser knows (`cozy`, `bluffing`, ...), and see it appear in a shortlist.

## Gotchas we hit

**`npm install` fails with `ERESOLVE` on `opik-langchain`.** `opik-langchain@2.3.4` declares a peer dependency of `opik@^1.8.75`, which conflicts with `opik@2.3.4`. Force the peer to the version you installed in `package.json`:

```json
"overrides": { "opik-langchain": { "opik": "$opik" } }
```

**The thread transcript is full of `{"message":{"value":...}}`.** Opik's thread view shows the root run's input and output. If your chain's root takes or returns an object, that object is what you see. Keep the root `Runnable<string, string>` and move bookkeeping (session id, shortlist) into `configurable` and inner steps, as `buildChain` does. `/chat-envelope` is the deliberate counterexample.

**The host answers "which of those is quickest to teach?" with invented facts.** The shortlist was recomputed each turn from what the guest typed, so games the host had just named could drop out, and the catalog has no teaching times anyway. Two fixes: `mentionedGames` keeps every game named earlier in the conversation in the shortlist, and the system prompt says to defer to staff for anything beyond player count and playtime. Before the fix the trace showed "10-15 minutes to learn"; after it, "A staff member will confirm the teaching time". You find this by opening the `ChatOpenAI` span and comparing the prompt to the answer.

## How it's put together

- `src/app.ts` - Fastify app: `/`, `/chat`, `/chat-envelope`; dependencies injected so tests can stub the model.
- `src/chain.ts` - the string chain, the envelope chain, and the shared `prepare-turn` step.
- `src/catalog.ts` - loads the catalog, parses guest wishes, shortlists, finds named games.
- `src/prompt.ts` - host system prompt and chat prompt template.
- `src/sessions.ts` - per-`sessionId` conversation memory.
- `src/tracing.ts` - the Opik client, one callback handler per session (`threadId`), flush.
- `src/server.ts` - wires the real model and handlers; `npm run dev` entry point.
- `src/demo.ts` - scripted guests, flush at the end.
- `public/index.html` - the chat widget.
- `data/games.json` - fictional 14-game catalog.
- `tests/catalog.test.ts`, `tests/app.test.ts` - shortlist and parser logic, the app with a fake model, and a turn through the real Opik handler with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
