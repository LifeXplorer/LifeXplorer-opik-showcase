# temporal-py-grant-review

*A grant application is reviewed by two OS processes and one flaky ledger call, and Opik shows it as a single trace.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Temporal](https://img.shields.io/badge/temporalio-1.37-000000?style=flat)
![OpenAI](https://img.shields.io/badge/model-gpt--4o--mini-412991?style=flat&logo=openai&logoColor=white)
![Opik](https://img.shields.io/badge/Opik-OTLP_ingestion-2f54eb?style=flat)

A neighbourhood fund gets grant applications as free text. Reviewing one is a short pipeline: a model screens the proposal, a ledger service says what is left in the relevant fund, a human-scale waiting period passes, and a model writes the decision letter. Temporal is a good fit because any step can die halfway, and a finished model call should never be paid for twice. The catch is observability: the code that *starts* the review (a client) and the code that *runs* it (a worker) live in different processes, so neither one has seen the whole story. This example wires both into Opik so the story comes back as one trace per application.

## What you'll build

- A `GrantReview` workflow with three activities: `screen_application` (LLM, returns category, requested amount, fit score), `check_budget` (reads a canned fund ledger and **fails on its first attempt on purpose**), and `draft_letter` (LLM). A 2-second durable timer sits between the ledger check and the letter.
- A launcher (`main.py`) that starts a local Temporal dev server on port 7290, spawns `worker.py` as a **separate OS process**, and reviews the two applications in `data/applications.json`: a garden that fits its fund and a youth band asking for more than its fund holds.
- Tracing in both processes: an OTLP exporter pointed at Opik's OpenTelemetry endpoint plus Temporal's `TracingInterceptor`, which carries the trace context from client to worker through Temporal's own headers.

## See it in Opik

Open the `temporal-py-grant-review` project and the Traces tab. You get two traces, `review:GR-2041` and `review:GR-2042`, each with **13 spans**, about 7 seconds long, and a cost of roughly $0.00012 to $0.00014 (about 420 to 450 tokens).

Expand one. The root `review:GR-2041` span was created by the client. Under it, `StartWorkflow:GrantReview` is also the client's, while `RunWorkflow:GrantReview`, every `StartActivity` / `RunActivity` pair and the model calls all came from the worker, yet they hang off the same tree. Check the span metadata to see it for yourself: the root span says `process: client, pid: 98627`, the two llm spans say `process: worker, pid: 98637` (your pids will differ).

Now find `check_budget`. It has two `RunActivity:check_budget` spans. The first is red, with the error `Ledger service unavailable: connection reset (transient, succeeds on retry)` and a stack trace in its metadata; the second, about a second later (the retry policy's 1 s initial interval), is clean. The 2-second timer shows up as the gap before `StartActivity:draft_letter`. The two `llm` spans, `screen-application` and `draft-decision-letter`, show the prompt, the reply, `gpt-4o-mini` and token usage, which is where the trace's cost comes from.

That is the answer to what Temporal's own UI can't tell you: not only "the workflow completed", but what the model said at each step, what it cost, and how many times a dependency had to be retried on the way.

## Run it yourself

1. `cd temporal-py-grant-review` and `cp .env.example .env`, then add `OPENAI_API_KEY` (a `.env` in a parent folder is found too). For Opik Cloud also set `OPIK_API_KEY`, `OPIK_WORKSPACE` and `OPIK_URL_OVERRIDE`; the defaults target a local Opik at `http://localhost:5173`.
2. `uv run main.py` (the Temporal dev server is downloaded on the first run; no Docker, no `temporal` CLI needed).
3. `uv run verify.py` to query Opik and check the shape described above.
4. Open the `temporal-py-grant-review` project in Opik and click the newest trace.

Tests: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`. They need no keys and never export anything.

## Poke around

- In `activities.py`, change `attempt == 1` to `attempt <= 3` and count the red `RunActivity:check_budget` spans; widen the gap with `backoff_coefficient=3` in `workflows.py` and measure it on the timeline.
- Raise `LEDGER["youth"]` above 9800 and compare the `draft-decision-letter` span input (`fund_remaining`, `decision`) and the letter it produces.
- Kill the worker mid-review (run `worker.py` against your own server with `TEMPORAL_ADDRESS`) and start it again: the workflow resumes from history and the finished screening call is not repeated.
- Remove `interceptors=[tracing_interceptor()]` from the client in `main.py` and check whether the worker's spans still join the client's root span.

## Gotchas we hit

**Custom span attributes are missing from the span metadata.** I set `process.pid` on a span and `pids=[]` came back from Opik. Opik's OTLP mapper keeps only attributes it knows; other attributes do not show up in the metadata. Put your own fields under `opik.metadata` as a JSON string: `span.set_attribute("opik.metadata", json.dumps({"process": "worker", "pid": os.getpid()}))`.

**`RunWorkflow` and `StartActivity` spans have a duration of 0.** Temporal's Python tracing records workflow-side spans as instantaneous events, so the span does not cover the workflow's wall time. Read the duration from the client's root span (`review:<id>`, 7.4 s here) and the `RunActivity` spans.

## How it's put together

- `main.py` - launcher and client: dev server, worker process, one traced review per application.
- `worker.py` - the worker process: tracing setup, workflow and activity registration, flush on SIGINT.
- `workflows.py` - the durable `GrantReview` workflow with its retry policy and timer.
- `activities.py` - screening, the flaky ledger check, the letter, and the traced `chat` helper.
- `otel.py` - OTLP exporter for Opik and the Temporal `TracingInterceptor`, shared by both processes.
- `models.py` - dataclasses and the task queue name.
- `verify.py` - queries Opik and checks traces, processes, retry error and cost.
- `data/applications.json` - two fictional applications.
- `tests/test_activities.py` - offline tests for parsing, the decision rule, the first-attempt failure, and a traced activity run with a stubbed model client.

---

*built with Opik · inspired by Opik's examples and documentation*
