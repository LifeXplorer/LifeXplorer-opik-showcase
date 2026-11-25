# langgraph-stargazing-rag

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/langgraph-1.2-1C3C3C?style=flat)
![Opik](https://img.shields.io/badge/opik-2.3-2f54eb?style=flat)

**A pocket handbook assistant for a fictional astronomy club, traced node by node, and a two-run experiment showing what retrieving too little costs.**

## The problem

A retrieval-augmented answer can be wrong in two quiet ways. The search can miss the passage that holds
the fact, or the model can invent a fact the passage never held. A fluent reply hides both. Here the
reader is a new member of the Brightwater Stargazers' Club asking about telescopes, dark-sky sites and
fees, and the assistant must answer from the club handbook or say it doesn't know.

## What you'll build

- A two-node LangGraph graph: `retrieve` pulls the `k` most similar handbook sections from an in-memory
  vector store (OpenAI `text-embedding-3-small`), and `generate` answers from them with `gpt-4o-mini`,
  or replies "The handbook doesn't say."
- A traced version of that graph. One call to `track_langgraph` makes each question a trace, each node a
  span, and the retrieval function its own `tool` span.
- An Opik dataset of 8 handbook questions, scored twice with `Hallucination` and `ContextPrecision`:
  once retrieving 1 section per question (`retrieval-k1`) and once retrieving 3 (`retrieval-k3`).

## See it in Opik

Open the project **langgraph-stargazing-rag** (workspace `default` on a local stack). The Traces tab holds
19 traces from one run. Three are the demo questions, rooted at a `LangGraph` span and tagged `k=3`.
Sixteen are experiment rows, rooted at an `evaluation_task` span.

Click a demo trace, such as "Can I buy a telescope through the club?". The tree reads `LangGraph`, then
`retrieve` with a `search_handbook` tool span inside it, then `generate` with a `ChatOpenAI` llm span inside
it. The tool span's output is the sections the search returned. The llm span shows the prompt, the reply, the
model (`gpt-4o-mini-2024-07-18`), the token counts (347 prompt tokens in the sample I opened) and a cost of
about $0.00007. In this run all 19 llm spans carried a cost.

Then open Experiments and select `retrieval-k1` and `retrieval-k3` together to compare them. Both rows hold
8 items, and the mean scores were:

| experiment | hallucination (0 = grounded) | context precision |
|---|---|---|
| `retrieval-k1` | 0.00 | 0.65 |
| `retrieval-k3` | 0.00 | 0.72 |

Hallucination is 0.00 in both runs, and that is the point. Find the question "What would a family
membership plus the loaner telescope deposit cost me in total?" The k=1 run retrieved one section, answered
"The handbook doesn't say.", and scored hallucination 0.0 and context precision 0.0. Saying "I don't know"
is honest, so the hallucination judge has nothing to flag, but it was a retrieval failure. The k=3 run
fetched both the fees and the loaner sections and answered "70 pounds ... plus 25 pounds ... 95 pounds"
at context precision 0.6. One metric measures honesty. The other is the one that notices a search miss.

Even k=3 is not perfect. Open "Which observing site should I use for a Milky Way session, and what do I
need to get in?" in either run. Both answers name Marrow Ridge but add that the handbook doesn't say how to
get in, although the gate-code sentence is in the handbook. That section never reached the model, and the
tool span's output shows it.

## Run it yourself

1. Put `OPENAI_API_KEY` in a `.env` (copy `.env.example`). The script loads this folder's `.env` and any
   `.env` found walking up from where you run it.
2. Point Opik at a backend: run `opik configure`, or set `OPIK_URL_OVERRIDE=http://localhost:5173/api/` and
   `OPIK_WORKSPACE=default` for a local stack.
3. `uv sync`
4. `uv run main.py`
5. Open the `langgraph-stargazing-rag` project in Opik. The run takes about two minutes and costs a few
   cents.

## Poke around

- Change `QUESTIONS` in `main.py` and look at `search_handbook`'s output next to the answer for each one.
- Run the experiments with `(1, 3, 5)` in `main.py`. Does the gate-code question get answered at k=5?
- Edit a figure in `docs/03-sites-and-events.md` (say, the family fee). The answer repeats the edit, and
  hallucination stays 0.0, because the metric checks the answer against the retrieved text, not the truth.
- Add a question the handbook can't answer to `DATASET_ITEMS` in `evaluation.py` and see how the two scores
  treat an honest "doesn't say".

## Gotchas we hit

- **`ImportError: cosine_similarity requires numpy to be installed` inside the `retrieve` task.**
  `InMemoryVectorStore` imports numpy lazily, and `langchain-core` doesn't depend on it, so the first
  search fails. Add `numpy` to your dependencies (`pyproject.toml` here lists `numpy>=2`).
- **The experiment traces have no `k=1` / `k=3` tags.** `OpikTracer(tags=[...])` only tags traces the tracer
  creates. Inside `evaluate()` the trace is created by the evaluation task and your tracer's tags don't
  reach it. Put the setting in `experiment_config={"k": k}` instead, which is shown on the experiment.
- **Experiment traces are rooted at `evaluation_task`, not `LangGraph`.** The graph run sits one level
  down (`task` then `LangGraph`), beside a `metrics_calculation` span holding the judge steps. Filter on
  the `search_handbook` span name instead of the root name when you want every retrieval.

## How it's put together

- `rag.py`: loads and chunks the docs, builds the graph, defines `search_handbook` (the `tool` span).
- `evaluation.py`: the 8-question dataset and `run_experiment` with the two judge metrics.
- `main.py`: wires up `track_langgraph`, answers three demo questions, then runs k=1 and k=3.
- `docs/`: four short handbook files; the whole corpus, split into 16 sections.
- `tests/`: offline tests with fake embeddings and a fake chat model. Run
  `OPIK_TRACK_DISABLE=true uv run pytest` with no provider keys. The graph test runs the `@opik.track`
  function with tracking off.

---

*built with Opik · inspired by Opik's examples and documentation*
