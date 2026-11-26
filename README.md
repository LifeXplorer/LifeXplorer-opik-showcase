# LifeXplorer · Opik showcase

**Twenty-three small, runnable LLM apps. Each one makes a single [Opik](https://github.com/comet-ml/opik) idea visible: a thread, a cost table, a failing test, a prompt that got better.**

![examples](https://img.shields.io/badge/examples-23-informational)
![python](https://img.shields.io/badge/python-3.12%2B-blue)
![typescript](https://img.shields.io/badge/typescript-node%2020%2B-3178c6)
![license](https://img.shields.io/badge/license-Apache--2.0-green)

Observability docs tend to show the happy path: wrap the client, see a trace. The interesting part comes after that.
Why did the specialist agent announce a handoff and then do nothing? Which of two models costs thirteen times more
for the same review? Did the extractor invent that cook time, or read it off the note? Every folder here is a
self-contained app, with fictional data and its own README, built so that one of those questions is answered by
opening one screen in Opik.

The examples were run against a local, self-hosted Opik. Every number quoted in a README comes from that run,
including the failures. Some suites deliberately stop at 4/6 or 6/8, because a red row teaches more than a green one.

## Pick an idea

### Conversations and threads
| Example | Stack | What you'll see in Opik |
|---|---|---|
| [`openai-ts-museum-guide`](openai-ts-museum-guide) | TypeScript · OpenAI + `opik-openai` | Each visitor conversation as one thread, cost per turn, a rating logged as feedback |
| [`langchainjs-fastify-boardgame-chat`](langchainjs-fastify-boardgame-chat) | TypeScript · LangChain.js + Fastify | Why a string-in/string-out root run makes threads read like transcripts, with a JSON-blob counter-example |
| [`vercel-ai-sveltekit-garden-helper`](vercel-ai-sveltekit-garden-helper) | TypeScript · Vercel AI SDK + SvelteKit | Streamed replies as traces, threads per chat, and a live online-evaluation rule grading every answer |
| [`langflow-makerspace-assistant`](langflow-makerspace-assistant) | Low-code · Langflow | A visual flow traced by Langflow's built-in Opik tracer, one span per component |

### Agents, tools and handoffs
| Example | Stack | What you'll see in Opik |
|---|---|---|
| [`openai-agents-insurance-claims`](openai-agents-insurance-claims) | Python · OpenAI Agents SDK | Triage → handoff → specialist trees, and a check that the specialist actually called its tools |
| [`mastra-energy-advisor`](mastra-energy-advisor) | TypeScript · Mastra (OTel) | Agent loops with real `execute_tool` spans and their arguments |
| [`voltagent-bike-repair-desk`](voltagent-bike-repair-desk) | TypeScript · VoltAgent (OTel) | How renaming OTel attributes to `gen_ai.*` turns untyped spans into priced llm and tool spans |
| [`beeai-py-aquarium-triage`](beeai-py-aquarium-triage) | Python · BeeAI (OpenInference) | A ReAct agent's model calls and tool lookups, plus the provider mapping that makes cost appear |
| [`smolagents-race-results-analyst`](smolagents-race-results-analyst) | Python · smolagents (OpenInference) | The pandas a CodeAgent wrote, and why one answer was wrong |
| [`crewai-wedding-planner`](crewai-wedding-planner) | Python · CrewAI | One kickoff trace with tokens and dollars split per agent |
| [`temporal-py-grant-review`](temporal-py-grant-review) | Python · Temporal | One trace spanning a client and a worker process, with the failed-then-retried activity |

### Cost and model comparison
| Example | Stack | What you'll see in Opik |
|---|---|---|
| [`litellm-code-review-router`](litellm-code-review-router) | Python · LiteLLM | The same diffs on gpt-4o-mini and Claude Haiku, with cost and latency side by side |
| [`opik-ts-translation-pipeline`](opik-ts-translation-pipeline) | TypeScript · Opik SDK only | A hand-built span tree with manual usage, server-computed cost and per-check feedback scores |

### Retrieval
| Example | Stack | What you'll see in Opik |
|---|---|---|
| [`langgraph-stargazing-rag`](langgraph-stargazing-rag) | Python · LangChain + LangGraph | retrieve → generate spans, and a k=1 vs k=3 experiment scored for hallucination and context precision |
| [`llamaindex-syllabus-qa`](llamaindex-syllabus-qa) | Python · LlamaIndex | Retrieval and synthesis spans over PDFs, plus a policy-level test suite with a 2-of-3 judge policy |
| [`quarkus-langchain4j-homebrew-rag`](quarkus-langchain4j-homebrew-rag) | Java · Quarkus + LangChain4j (OTLP) | JVM traces over OTLP with the full prompt, retrieved chunks and completion on the llm span |

### Evaluation, suites and prompt improvement
| Example | Stack | What you'll see in Opik |
|---|---|---|
| [`pydantic-ai-recipe-extraction`](pydantic-ai-recipe-extraction) | Python · Pydantic AI (OTel) | Typed output plus a test suite that catches invented values |
| [`dspy-chess-openings-qa`](dspy-chess-openings-qa) | Python · DSPy | The same suite before and after compiling: 0/8 → 6/8 |
| [`optimizer-podcast-topic-classifier`](optimizer-podcast-topic-classifier) | Python · Opik Agent Optimizer | A score curve across trials, with the winning prompt saved as a new library version |

### Images, audio and attachments
| Example | Stack | What you'll see in Opik |
|---|---|---|
| [`openai-py-storybook-illustrator`](openai-py-storybook-illustrator) | Python · OpenAI images | Generated pages attached to their traces, and the brief evolving from v1 to v2 in the prompt library |
| [`openai-vision-shipping-labels`](openai-vision-shipping-labels) | Python · OpenAI vision | Label images on every trace, and a suite that fails honestly on faded print |
| [`whisper-birding-field-notes`](whisper-birding-field-notes) | Python · OpenAI TTS + transcription | A playable MP3 on each trace, and judge flakiness absorbed by an execution policy |

### Zero-code
| Example | Stack | What you'll see in Opik |
|---|---|---|
| [`n8n-foodbank-volunteer-screening`](n8n-foodbank-volunteer-screening) | Low-code · n8n in Docker | Every workflow run and node traced through hooks, with no instrumentation in the workflow |

## Running one

1. Have an Opik to send to. The quickest is a local self-hosted stack from the
   [Opik repo](https://github.com/comet-ml/opik) (`./opik.sh`, then the UI on `http://localhost:5173`). To use Opik
   Cloud instead, set the Cloud variables in `.env`.
2. `cp .env.example .env` at the repo root and add your `OPENAI_API_KEY`. The LiteLLM example also wants
   `ANTHROPIC_API_KEY`. Examples find this file by walking up from their own folder.
3. `cd` into a folder and follow its README. The commands are short:
   - Python: `uv run main.py` (or the package entry point the README names), tests with `uv run pytest`
   - TypeScript: `npm install && npm run demo`, tests with `npm test`
   - Java: `./run.sh`
   - n8n: `./setup.sh && ./demo.sh` (needs Docker)

The tests in the Python and TypeScript examples run offline: no provider key, no Opik, a few seconds.

A typical run costs well under a cent. The image, audio and test-suite examples cost a few cents.

## What's in a folder

Every example follows the same anatomy, so you can skim them quickly:

- `README.md`: the problem, what to open in Opik and what you'll see there, how to run it, things to try, and a
  **Gotchas** section of real problems hit while building it, each with symptom, cause and fix
- the app: small enough to read in one sitting, with every Opik touchpoint commented on why it's there
- `data/` or `docs/`: fictional inputs (no real customers, people or datasets)
- `tests/`: offline unit tests, including one that runs a traced function with tracking switched off
- `.env.example`: just the variables that example reads

The git history is worth a look too. Most examples arrive as a plain app first, and the next commits add Opik. The
diff between them is the change you'd make to your own code.

## License

[Apache 2.0](LICENSE).

---

<sub>Built with Opik · inspired by Opik's [examples](https://github.com/comet-ml/opik) and
[documentation](https://www.comet.com/docs/opik/).</sub>
