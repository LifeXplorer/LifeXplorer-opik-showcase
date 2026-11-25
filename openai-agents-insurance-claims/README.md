# openai-agents-insurance-claims

*A claims hotline where one agent triages and two specialists work, and Opik shows who actually did the work.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![openai-agents](https://img.shields.io/badge/openai--agents-0.26-412991?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.3.4-2f54eb?style=flat)

## The problem

In a handoff-based agent, "the claim went to the right specialist" is not the same as "the claim was handled". A routing check on the last agent name happily passes when the specialist replies with small talk and never opens the policy. The answer looks plausible; the evidence is only in the span tree.

## What you'll build

A triage agent and two specialists (`Auto Claims Agent`, `Property Claims Agent`) on `gpt-4o-mini`. Specialists share three function tools over a fictional policy file in `data/policies.json`: `lookup_policy`, `estimate_payout`, `open_claim`. Three scripted conversations run with no human input: a parking-lot fender bender, a burst pipe, and a stolen car on a lapsed policy. Tracing is one line, `set_trace_processors([OpikTracingProcessor()])`; each turn runs inside `trace(..., group_id=...)` so the turns of one claim become one Opik thread. `verify.py` then reads the traces back and checks each thread for a handoff span and at least one tool span per turn.

## See it in Opik

Open the `openai-agents-insurance-claims` project. After one clean run it holds 5 traces named `Claims intake` in 3 threads, 61 spans (17 `llm`, 7 `tool`, 37 `general`) and about 8.9k tokens, roughly $0.0016 in total.

Open the `fender-bender` thread: two traces. In the first, the tree reads `Claims Triage Agent` → `Handoff` → `Auto Claims Agent`, and under the specialist you see `lookup_policy` then `estimate_payout` with the arguments the model chose (`POL-1001`, `1800`) and the JSON returned (`estimated_payout_usd: 1300`). The second turn shows `open_claim` returning a `CLM-` id. Open `lapsed-policy`: a single trace where the specialist calls only `lookup_policy`, sees `active: false`, and declines to open a claim.

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY` (or keep it in a parent `.env`, which is found automatically).
2. `uv sync`
3. `uv run main.py` (about 30 seconds)
4. `uv run verify.py` to print per-thread handoff/tool results from Opik.
5. `uv run pytest` for the offline tests (set `OPIK_TRACK_DISABLE=true`, no keys needed).

## Poke around

- Add a "storm took shingles off my roof and dented my car" conversation and see which specialist triage picks at the `Handoff` span.
- Delete `SPECIALIST_RULES` from the specialists and rerun `verify.py` to bring the failure below back.
- Make `estimate_payout` raise an error and look at how the tool span records it.
- Add a third specialist (fraud review) and note that the new handoff appears with no tracing changes.

## Gotchas we hit

**Symptom:** `lapsed-policy` routes correctly (`routed_to: Auto Claims Agent`) but the reply is "I'm transferring you to an Auto Claims Agent..." and `verify.py` prints `FAIL ... turn 1: specialist made no tool calls`. In Opik the trace has a `Handoff` span and an `Auto Claims Agent` span with no `tool` spans.

**Cause:** after the handoff the specialist had no hint that it was the one who should act, so it narrated the transfer instead of calling tools.

**Fix:** prefix specialist and triage instructions with the SDK's handoff prompt and say plainly that the specialist does the work:

```python
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
instructions = RECOMMENDED_PROMPT_PREFIX + "You ARE the specialist ... Always call lookup_policy before replying."
```

After the change the same conversation shows a `lookup_policy` tool span and a refusal explaining the lapsed policy.

## How it's put together

- `main.py` — agents, tools, scripted conversations, tracing setup and thread grouping.
- `claims_core.py` — plain policy lookup, payout and claim logic, no agent or tracing code.
- `data/policies.json` — four fictional policies (one lapsed).
- `verify.py` — reads traces back from Opik and checks handoff and tool spans per thread.
- `tests/test_claims.py` — offline tests: claim logic, a turn under `trace()` with tracking disabled, routing scoring, span-tree checks.
- `.env.example` — the keys needed.

*built with Opik · inspired by Opik's examples and documentation*
