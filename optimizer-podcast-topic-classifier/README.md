# optimizer-podcast-topic-classifier

*Let an optimizer rewrite a chatty podcast-topic prompt, and watch the score curve prove it worked.*

![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue?style=flat)
![opik-optimizer 3.2](https://img.shields.io/badge/opik--optimizer-3.2-orange?style=flat)
![uv](https://img.shields.io/badge/setup-uv-de5fe9?style=flat)

Nightlight Audio is a fictional podcast network that wants every new episode filed under one of five topics: `science`, `history`, `business`, `true-crime`, `culture`. The first prompt anyone writes for this is friendly and vague, and the model answers in friendly, vague sentences ("This episode blurb belongs to a science show."). A downstream system that wants the exact word `science` rejects every one of them. Fixing this by hand means guessing; this example fixes it with a measured loop instead.

## What you'll build

A small package, `podcast_topics/`, that does three things in order:

1. Classifies 25 labeled episode blurbs with the baseline prompt (plain OpenAI calls, `gpt-4o-mini`) and prints the exact-match accuracy.
2. Uploads the blurbs as an Opik dataset and hands the baseline to `MetaPromptOptimizer`, capped at 4 trials.
3. Saves the baseline as version 1 and the winner as version 2 of the `podcast-topic-classifier` prompt in the Opik prompt library.

In my run the baseline scored **0.00** (not one answer was a bare label) and the optimizer's best prompt scored **0.76**.

## See it in Opik

Everything lands in the project `optimizer-podcast-topic-classifier` on your local Opik (`http://localhost:5173`, workspace `default`).

- **Optimization runs.** The script prints a project-pinned link at the end. Open it: you get one optimization, status `completed`, over the dataset `optimizer-podcast-topic-classifier-episodes`. The trial list shows five scored candidates in the order they ran: 0.00 (the baseline), 0.00, 0.76, 0.00, 0.76. The baseline's 0.00 comes from full-sentence answers; the winner demands a single-word answer. Click any trial to read the prompt it tried and its 25 per-episode results.
- **Traces tab.** 152 traces in total: 25 named `classify_episode` (the plain baseline pass, each with one `llm` span for `gpt-4o-mini`), 125 named `evaluation_task` (5 scored runs x 25 episodes), and 2 `optimization_algorithm` traces where the optimizer reasons about the failures. Every `llm` span carries token usage and an estimated cost.
- **Prompts tab.** `podcast-topic-classifier` has two versions: v1 is the friendly baseline, v2 is the winning wording ("...Provide a single-word response reflecting the category."). Versions are immutable, so an app can pin v2 and roll back by pinning v1.
- **Datasets tab.** `optimizer-podcast-topic-classifier-episodes` holds the 25 labeled blurbs.

## Run it yourself

1. `cd optimizer-podcast-topic-classifier`
2. Put `OPENAI_API_KEY` in a `.env` (see `.env.example`; a `.env` in any parent folder works too) and make sure `opik` is configured for your instance (`opik configure`, or `OPIK_URL_OVERRIDE` + `OPIK_WORKSPACE`).
3. `uv sync`
4. `uv run python -m podcast_topics` (about a minute; a few cents of `gpt-4o-mini`)
5. Open the "optimization run" link it prints, then the Prompts tab.

Scores will wobble between runs: the optimizer proposes different candidates each time.

## Poke around

- Raise `MAX_TRIALS` in `podcast_topics/optimize.py` to 8 and see whether a later trial beats 0.76.
- The metric is strict. Loosen `normalize` in `metric.py` so "true crime" counts as `true-crime` and see how the curve changes.
- Add a sixth topic to `episodes.py` (and `TOPICS`) and re-run; does the optimizer rediscover the output contract?
- Rewrite `BASELINE_SYSTEM` with "answer with only the label" and watch the baseline jump on its own.

## Gotchas we hit

- **Symptom:** the printed `result.get_run_link()` opens a run that looks empty. **Cause:** the link keeps whatever project the UI last showed, and the trial list is scoped to a project. **Fix:** build a project-pinned URL from the optimization's own project id: `client.rest_client.optimizations.get_optimization_by_id(result.optimization_id).project_id`, then `<ui>/<workspace>/projects/<project_id>/optimizations/<optimization_id>`.
- **Symptom:** the saved library prompt shows a literal `{episode}` and never fills in. **Cause:** the optimizer formats variables with single braces, the prompt library uses mustache `{{episode}}`. **Fix:** convert before saving, as `to_library_messages` does.
- **Symptom:** `total llm cost : unavailable` even though the spans show costs. **Cause:** `result.llm_cost_total` came back `None` for this run. **Fix:** read cost from the `llm` spans in the project instead; the script just prints "unavailable".

## How it's put together

- `podcast_topics/episodes.py` - 25 labeled blurbs and the topic list.
- `podcast_topics/prompts.py` - baseline prompt, user template and the brace converter for the library.
- `podcast_topics/metric.py` - strict exact-match accuracy.
- `podcast_topics/classifier.py` - the traced classifier (`track_openai` plus `@opik.track`).
- `podcast_topics/optimize.py` - dataset, library v1, the optimizer run and the v2 save.
- `podcast_topics/__main__.py` - baseline pass, then the optimization.
- `tests/test_app.py` - offline tests: metric, data shape, brace conversion, and a traced call with tracking disabled.

Run the tests with `OPIK_TRACK_DISABLE=true uv run pytest` (no keys needed).

*built with Opik · inspired by Opik's examples and documentation*
