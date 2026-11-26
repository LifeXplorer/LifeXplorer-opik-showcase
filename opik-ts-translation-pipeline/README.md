# opik-ts-translation-pipeline

![Node](https://img.shields.io/badge/node-20%2B-339933?style=flat&logo=nodedotjs&logoColor=white)
![Opik](https://img.shields.io/badge/opik-2.3.4-2f54eb?style=flat)
![Tests](https://img.shields.io/badge/tests-vitest-6E9F18?style=flat)

*A localization QA pipeline for UI strings, traced span by span with nothing but the Opik TypeScript SDK.*

Machine-translated UI strings fail in quiet ways: a `{count}` placeholder vanishes, a glossary term gets
paraphrased, a label grows too long for its button. When a reviewer asks "why was this string approved?",
a single opaque model call is no answer. This example builds the pipeline by hand so each decision has its own
span, and each check has its own score.

## What you'll build

A script that localizes five strings from a fictional tide-tracking app, *Tidepool*, into German
(`data/strings.json`). For each string it runs four stages:

```
localize-string (trace)
 ├─ translate        general   └─ chat gpt-4o-mini   llm
 ├─ back-translate   general   └─ chat gpt-4o-mini   llm
 ├─ quality-checks   tool      placeholders, glossary, length, round-trip similarity
 └─ decide           guardrail pass / review verdict
```

Nothing wraps the OpenAI client. `src/tracing.ts` opens the spans and copies the model, provider and token counts
onto each `llm` span itself. `src/pipeline.ts` opens the `tool` and `guardrail` spans, attaches three feedback
scores to the trace and tags it with the verdict. `src/demo.ts` ends with `await opik.flush()`.

## See it in Opik

Open the **opik-ts-translation-pipeline** project (workspace `default`). In my verified run it held
**5 traces and 30 spans**: one `localize-string` trace per string, each with six spans (two stage spans, two `llm`
spans, one `tool`, one `guardrail`).

- **Traces tab.** Every row is tagged `pass` or `review`, so you can filter on the tag. The
  feedback-scores columns show `placeholder-integrity`, `glossary-compliance` and `backtranslation-similarity`.
  In my run the similarity scores were 0.75, 1, 0.71, 0.75 and 1. Hover a score to read its reason; the
  similarity reason holds the back-translation text.
- **Open one trace.** The tree shows `translate` and `back-translate`, each with a `chat gpt-4o-mini` child. Click a
  child: model `gpt-4o-mini-2024-07-18`, provider `openai`, and token usage (for example 60 prompt and 17 completion
  tokens) were written by hand. A cost appears next to them (about $0.00002 per call), computed by Opik from those fields.
  The whole run cost about $0.0002 in Opik, so five strings are essentially free.
- **`quality-checks` span.** Its output is the full result object, so you can see the length ratio and which
  placeholders were found. The `decide` span's output lists the reasons behind a `review`.

Model output varies between runs. In my first, unrecorded run one string (`alert.slack_water`) came back as
"Still water ... Reel in your fishing rods" and landed in `review` with similarity 0.44; in the verified run all five passed.
Run it a few times and you will see both outcomes.

## Run it yourself

1. Start Opik, or point the SDK at Opik Cloud, and set `OPIK_URL_OVERRIDE` (and `OPIK_WORKSPACE`, `OPIK_API_KEY` if needed).
   For a local stack: `export OPIK_URL_OVERRIDE=http://localhost:5173/api/ OPIK_WORKSPACE=default`.
2. `cp .env.example .env` and add `OPENAI_API_KEY`.
3. `npm install`
4. `npm run demo`
5. Open the project above and expand the newest traces.

## Poke around

- Delete `await opik.flush()` in `src/demo.ts` and run again. The decisions print as usual, but the batch can be
  lost when the process exits before the SDK's background queue sends it.
- Remove the `usage:` and `model:` lines from the `llm` span in `src/tracing.ts`. The call still traces, but the
  token and cost columns go empty.
- Raise `MIN_SIMILARITY` in `src/qa.ts` to 0.8, or drop a glossary entry from the system prompt in `src/prompts.ts`, and
  watch more traces turn up as `review`, with the reasons on the `decide` span.
- Change `"type": "guardrail"` on the `decide` span to `"general"` and compare how the tree renders it.

## Gotchas we hit

- **`Type 'CheckResult' is not assignable to type 'JsonListString'` (and `Record<string, unknown>`).** Span
  `input` and `output` expect an index-signature object. A TypeScript `interface` has none, so passing one fails to
  compile. Declare span payloads with `type X = { ... }` (see `src/types.ts`) or spread them into a plain object.
- **"Started logging traces to the project ..." prints even with `OPIK_TRACK_DISABLE=true`.** The line is only
  the client's startup message. With the variable set, a stub server saw no requests from the hand-built traces and
  spans, while the same code without it posted to `/traces/batch` and `/spans/batch`. Set the variable in the
  test environment (`OPIK_TRACK_DISABLE=true npm test`) and ignore the log line.

## How it's put together

- `src/demo.ts`: loads the corpus, runs each string, prints verdicts, flushes.
- `src/pipeline.ts`: the trace, the tool and guardrail spans, the feedback scores and the verdict tag.
- `src/tracing.ts`: the Opik client and the traced model-call stage (stage span plus `llm` span with usage).
- `src/llm.ts`: a thin OpenAI wrapper behind a small interface, so tests can stub it.
- `src/prompts.ts`: translation and back-translation prompts, including the glossary.
- `src/qa.ts`: the pure checks (placeholders, glossary, length, similarity) and the decision rule.
- `src/types.ts`: shared types.
- `data/strings.json`: the fictional strings and glossary.
- `tests/qa.test.ts`: unit tests for every check and the verdict.
- `tests/pipeline.test.ts`: runs the traced pipeline with a stub model and tracking disabled.

Run the tests with no keys: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true npm test`.

---

*built with Opik · inspired by Opik's examples and documentation*
