# openai-ts-museum-guide

A visitor-guide chatbot for a fictional clock museum, traced into Opik so every conversation reads as a thread.

## What you'll build

A TypeScript chatbot on the OpenAI SDK, wrapped with `opik-openai`. Each visitor turn is one trace, turns of one conversation share a `threadId`, and a rating is logged as a feedback score after the run.

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY` (or use a repo-root `.env`).
2. `npm install`
3. `npm run demo`
4. Open the `openai-ts-museum-guide` project in Opik and check Logs and Threads.

## Gotchas we hit

### `npm install opik opik-openai` fails with ERESOLVE

`opik-openai` declares a stale peer dependency (`opik@^1.8.61`) while the current `opik` is 2.x. Add an override that pins it to your `opik`:

```json
"overrides": { "opik-openai": { "opik": "$opik" } }
```

---

*built with Opik · inspired by Opik's examples and documentation*
