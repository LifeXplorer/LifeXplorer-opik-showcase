<div align="center">

# litellm-code-review-router

**Send the same pull-request diffs to two models and read the price of each in one table.**

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LiteLLM](https://img.shields.io/badge/litellm-1.79%2B-1C7ED6?style=flat)
![Opik](https://img.shields.io/badge/opik-2.3.4-2f54eb?style=flat)

</div>

Code-review summaries are a perfect "cheap model or better model?" workload: short input, structured output, and a team that reads hundreds a week. Picking the model by gut feel is expensive, and comparing providers by hand means juggling two SDKs and two billing pages. `review-router` is a small command-line package that routes five fictional pull-request diffs to `gpt-4o-mini` and `claude-haiku-4-5` through LiteLLM, logs every call to Opik, and can rebuild the per-model cost and latency table from Opik alone.

## What you'll build

A Python package with a `review-router` command. `run` loads the diffs in `data/diffs/`, sends each one to every model with one shared reviewer prompt (a one-line summary, up to three risks, a verdict), prints a table from LiteLLM's own numbers, and ends with a run id. `compare <run-id>` then ignores the local numbers entirely: it asks Opik for every llm span tagged with that run and prints the same table, so you can check that what Opik stored is what you paid. Each review is a `review_diff` function wrapped in `@opik.track`; LiteLLM's `OpikLogger` callback logs the model call inside it.

## See it in Opik

Open the `litellm-code-review-router` project. One `run` leaves **10 traces**, all named `review_diff`, each with three tags such as `model:claude-haiku-4-5-20251001`, `diff:03-sql-search` and `run:4fd72a67`. Type a model tag or a run tag into the filter and the table narrows to that model or that run. Sort by **Estimated cost**: the five `gpt-4o-mini` traces sit around $0.00008 to $0.00010, the five Haiku ones around $0.0010 to $0.0013.

Open any trace and you see a `review_diff` span with one child, an `llm` span named after the model. The child carries the provider (`openai` or `anthropic`), prompt and completion tokens, the cost, and the full prompt and answer, so when the cheaper model's verdict looks off you can read exactly why. In our run the project held 10 traces and 20 spans (10 general, 10 llm).

The totals, identical in the local table and in `compare`:

| model | calls | tokens | cost | mean latency |
|---|---|---|---|---|
| gpt-4o-mini | 5 | 1,559 | $0.000454 | 1.80s |
| claude-haiku-4-5 | 5 | 2,232 | $0.005928 | 2.45s |

Haiku was 13.0x more expensive and a bit slower on this workload, partly from its higher per-token price and partly because it wrote longer reviews (2,232 tokens against 1,559 for the same diffs). The whole run cost under a cent.

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`. Local Opik needs no key; for Opik Cloud fill in the Opik block too.
2. `uv sync`
3. `uv run review-router run` (add `--show` to print each review, `--diff sql` to review one diff, `--model openai/gpt-4.1-mini` to choose models).
4. Copy the printed run id and run `uv run review-router compare <run-id>`.
5. Open the `litellm-code-review-router` project in Opik and sort the traces by Estimated cost.

## Poke around

- Add a third model with `--model openai/gpt-4o-mini --model anthropic/claude-haiku-4-5-20251001 --model gemini/gemini-2.0-flash` (needs `GEMINI_API_KEY`) and watch a third row appear in both tables with no code change.
- Edit `SYSTEM_PROMPT` in `review_router/prompts.py` to ask for "at most two sentences" and re-run. The cost gap narrows because the extra Haiku cost is mostly output tokens.
- Run `review-router run` twice, then filter the trace table by each `run:` tag to compare two runs of the same models.
- Drop your own `.diff` file into `data/diffs/`; it is picked up on the next run.

## Gotchas we hit

**Startup prints `RuntimeError: no running event loop` and a "coroutine was never awaited" warning.** Cause: LiteLLM's `OpikLogger` tries to start a background flush task in its constructor, which fails in a plain synchronous script. It then falls back to sending synchronously, so nothing is lost. Fix: mute LiteLLM's logger and that one warning while constructing it, as `review_router/tracing.py` does:

```python
litellm_log.setLevel(logging.CRITICAL)
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=".*periodic_flush.*", category=RuntimeWarning)
    litellm.callbacks = [OpikLogger()]
```

**The model column in Opik says `gpt-4o-mini-2024-07-18`, not the `openai/gpt-4o-mini` you passed.** Cause: the llm span records the model name the provider reports in its response. Fix: nothing is broken, but anything that groups by model (like `compare`) sees the dated name. Use the `model:` tag, which holds the name you asked for, when you want to filter by your own label.

## How it's put together

- `review_router/cli.py`: the `run` and `compare` commands.
- `review_router/router.py`: `review_diff` (one model, one diff, traced with `@opik.track`) and `run_all`.
- `review_router/tracing.py`: attaches LiteLLM's `OpikLogger` and flushes at exit.
- `review_router/opik_report.py`: reads a run's llm spans back from Opik.
- `review_router/report.py`: groups samples per model and renders the table.
- `review_router/prompts.py`, `diffs.py`, `config.py`: the shared reviewer prompt, the diff loader, the model list and project name.
- `data/diffs/`: five fictional pull-request diffs.
- `tests/`: offline tests with a stubbed `litellm.completion`, including a call to the traced function with tracking disabled. Run `OPIK_TRACK_DISABLE=true uv run pytest` (no keys needed).

---

*built with Opik · inspired by Opik's examples and documentation*
