# llamaindex-syllabus-qa

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LlamaIndex](https://img.shields.io/badge/llama--index-0.14-6a4c93?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.3-2f54eb?style=flat)

**Ask three course syllabi about late penalties and AI rules, then watch Opik show whether the right course answered.**

"What happens if I'm two days late?" has a different answer in every course. A student-services bot that
returns BIO 214's 10%-per-day rule for a CS 330 question is wrong in a way that reads as perfectly fluent.
When that happens you need to know which half of the pipeline slipped: did retrieval fetch the wrong
course's section, or did the model misread the right one? This example puts both halves on screen, and then
pins the policies down in a test suite so a regression shows up as a number.

## What you'll build

- Three fictional syllabi (BIO 214 Marine Ecology, CS 330 Applied Cryptography, HIS 101 Maritime History),
  rendered to PDF by `syllabus_qa/corpus.py`. The courses deliberately disagree: 10% per 24 hours versus
  4 slip days versus one 48-hour token; AI summarising allowed versus AI debugging allowed versus AI banned.
- A LlamaIndex query engine over the PDFs: `text-embedding-3-small` embeddings, 128-token chunks so a policy
  section is one chunk, top 4 retrieved, answered by `gpt-4o-mini`.
- Opik's `LlamaIndexCallbackHandler`, which logs each question as a trace with retrieval and synthesis spans.
- An Opik test suite of 8 policy questions with plain-English assertions, two suite-wide rules, and an
  execution policy of 3 runs per item with 2 required to pass, judged by Opik's LLM judge.

## See it in Opik

Open the `llamaindex-syllabus-qa` project (http://localhost:5173 for a local stack).

- **Traces tab, name `query`.** One run leaves 4 of these, one per demo question. Open the HIS 101
  office-hours one. It has seven spans: `retrieve` with an `embedding` child, and `synthesize` with two
  `chunking` children, a `templating` span and an `llm` span. The `retrieve` output lists the chunks that
  came back (four HIS 101 sections for this question). The `llm` span is `gpt-4o-mini`, about 540 prompt
  tokens, around $0.00009. Compare it with "Which of the three courses prohibits AI tools": retrieval
  there returns chunks from HIS 101, CS 330 and BIO 214, which is what the model needs to compare courses.
- **Traces tab, name `evaluation_task`.** 24 more: 8 questions times 3 runs. Each one nests the same
  `query` span (with retrieve and synthesize underneath) inside a `task` span, next to the judge's
  `llm_judge` and `completion` spans (the judge ran on `gpt-5-nano`). Failures can be traced the same way
  as the demo questions.
- **Test suites, then `syllabus-policies`.** The suite has 8 items. The experiment run `gpt-4o-mini-top4`
  scored 8 of 8 items. One item, "Is there extra credit in BIO 214?", passed 2 of 3 runs. The BIO 214
  syllabus is silent on it while CS 330 and HIS 101 each say "no extra credit", which makes it the item most
  likely to wobble. The execution policy let it pass; open the item to see the run the judge rejected.
- Whole project: 28 traces, 340 spans, 52 `llm` spans, every one with token usage and cost (about
  $0.01 across the app and the judge).

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and have Opik reachable (local stack, or Opik Cloud via `opik configure`).
2. `cp .env.example .env` and set `OPENAI_API_KEY` (a `.env` in any parent folder is found too).
3. `uv sync`
4. `uv run main.py`. It takes about 40 seconds and costs under two cents.
5. Open the experiment link printed at the end, then the project's Traces tab.
6. `uv run pytest` runs the offline tests (no keys, no network).

The PDFs are committed in `data/syllabi/`; delete them and the app regenerates them on the next run.

## Poke around

- Change `TOP_K` in `syllabus_qa/engine.py` from 4 to 1, re-run, and see which `evaluation_task` traces lose
  the chunk they needed: the AI-rules question depends on several courses being retrieved together.
- Edit a number in `corpus.py` (make BIO 214 deduct 15% per 24 hours), delete `data/syllabi/`, re-run: the
  suite fails the BIO 214 items and nothing else.
- Remove the course code from one policy sentence in `corpus.py` and ask the CS 330 slip-day question;
  check whether retrieval still lands on the right chunk.
- Set `pass_threshold` to 3 in `suite.build_suite` (on a new suite name) and see how many items stop passing.

## Gotchas we hit

**"ValueError: No files found in .../data/syllabi" even though the PDFs are there.** `SimpleDirectoryReader`
skips any path with a dot-folder in it, and this checkout sits under one. Pass files instead of a
directory: `SimpleDirectoryReader(input_files=[str(p) for p in pdfs])`.

**An offline test prints `OPIK: Unauthorized message type 'CreateTraceBatchMessage'`.** The LlamaIndex
handler talks to the Opik client directly and ignores `OPIK_TRACK_DISABLE=true`, so tests that attach it
still send traces. `tracing.enable_tracing()` therefore returns early when `opik.is_tracing_active()` is
false.

**The suite fails answers that are correct.** Two causes, both seen in our first runs. An assertion like
"the answer says 10% per 24 hours, so 20% at 48 hours" fails when the answer only says 20%, because the judge
looks for the wording in the answer, not in the excerpts. And the global "invents no figures" rule flagged
20% as invented, since only 10% per 24 hours appears in the text. Assert the outcome ("loses 20% of its
mark") and say in the global rule that plain arithmetic on a retrieved rate is allowed.

## How it's put together

- `main.py`: loads `.env`, turns on tracing, asks the demo questions, flushes, runs the suite.
- `syllabus_qa/corpus.py`: the three syllabi as data, PDF rendering, regenerate-if-missing.
- `syllabus_qa/engine.py`: models and chunking, index build, answer prompt, `ask()` returning text plus sources.
- `syllabus_qa/questions.py`: the four demo questions.
- `syllabus_qa/tracing.py`: attaches Opik's callback handler to LlamaIndex.
- `syllabus_qa/suite.py`: the 8 policy items, the global assertions, the execution policy, `run_suite`.
- `data/syllabi/`: the generated PDFs.
- `tests/test_corpus.py`: course codes in every policy, PDF round-trip, regeneration.
- `tests/test_suite.py`: suite shape, course mapping, task output for the judge, result summary.
- `tests/test_tracing.py`: a real LlamaIndex query with mock models and tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
