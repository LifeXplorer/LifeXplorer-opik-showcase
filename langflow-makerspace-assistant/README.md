<div align="center">

# Sprocket, the makerspace front desk, in Langflow

**`langflow-makerspace-assistant`**

*A drag-and-drop chat flow with zero tracing code, and every question still shows up in Opik.*

![Langflow](https://img.shields.io/badge/Langflow-1.8.4-7c3aed?style=flat)
![Model](https://img.shields.io/badge/model-gpt--4o--mini-412991?style=flat&logo=openai&logoColor=white)
![Opik](https://img.shields.io/badge/Opik-1.10.52-2f54eb?style=flat)
![Python](https://img.shields.io/badge/python-3.12-3776AB?style=flat&logo=python&logoColor=white)

</div>

---

Visual flow builders put LLM apps in the hands of people who will never open an editor, so there is nowhere to paste a tracing decorator. Langflow solves that on its side: if its server can see an Opik destination in the environment, every flow run is reported to Opik on its own. This example proves it with a small, concrete app: Sprocket, the chat assistant at the fictional Quillmere Makerspace, which answers questions about booking machines, earning badges, safety rules and opening hours.

## What you'll build

A Langflow flow (four components: Chat Input, Prompt Template, Language Model, Chat Output) shipped as importable JSON in `flows/`. The Prompt Template holds the whole member guide from `docs/makerspace-guide.md`, and gpt-4o-mini answers from it. `demo.py` runs the full show headlessly: it starts Langflow on port 7870, imports the flow through Langflow's REST API, asks three scripted questions in one chat session (a booking question, a safety trap about cutting vinyl, and opening hours), then shuts the server down.

```
question ──► Langflow flow ──► gpt-4o-mini ──► answer
                  │
                  └──► Opik (Langflow's own tracer): trace, component spans, llm span with tokens + cost
```

There is no Opik import anywhere in this repo's code. The only "integration" is four environment variables that `demo.py` hands to the Langflow server process.

## See it in Opik

Open the project **`langflow-makerspace-assistant`** in your Opik instance.

- **Traces tab:** three traces, one per question. Each trace is named after the flow's id (a UUID), and its metadata carries `flow_name: Makerspace Assistant`, `created_from: langflow` and the elapsed time. Input and output hold every component's payload, so you can read the exact prompt Langflow assembled.
- **Thread:** the three traces share one thread id (`member-xxxxxxxx`, the session id the demo sends), so the **Threads** tab shows them as a single conversation. Langflow forwards the session id, but this basic flow has no memory component, so the model does not see earlier turns: the prompt stays near 740 tokens each time.
- **Inside a trace:** five spans. Four `general` spans, one per component (Chat Input, Prompt Template, Language Model, Chat Output), and under the Language Model span one `llm` span from the LangChain callback, with model `gpt-4o-mini-2024-07-18`, provider `openai`, and usage. In the verified run the three questions used 744, 738 and 725 prompt tokens and 41, 45 and 38 completion tokens, about 1.0 to 1.3 seconds each.
- **Cost:** each trace is priced automatically, roughly $0.00013 to $0.00014, so $0.0004 for the whole demo.
- **The safety trap:** open the vinyl trace and check the answer refuses the cut and mentions toxic gas. Rule 4 of the guide is the only reason it can.

## Run it yourself

1. Have a running Opik (self-hosted at `http://localhost:5173` by default) and an OpenAI key.
2. `cp .env.example .env` and set `OPENAI_API_KEY` (a `.env` in any parent folder works too). Adjust `OPIK_URL_OVERRIDE` / `OPIK_WORKSPACE` if your Opik lives elsewhere; for Opik Cloud see the comments in `.env.example`.
3. `uv sync --python 3.12` (Langflow is a heavy install, allow a few minutes the first time).
4. `uv run python demo.py`. The whole run takes about half a minute.
5. Open the `langflow-makerspace-assistant` project in Opik.

Everything Langflow writes (SQLite database, keys) goes to a throwaway temp folder, and the printed path at the end holds `server.log`.

## Poke around

- Edit `docs/makerspace-guide.md` (say, change Sunday hours), run `uv run python build_flow.py` to rebuild the flow JSON, rerun the demo, and diff the two prompts in Opik.
- Add a fourth question to `QUESTIONS` in `demo.py` that the guide does not cover ("Do you sell filament?") and see whether Sprocket sends you to the front desk.
- In `build_flow.py`, swap `gpt-4o-mini` for another OpenAI model and compare per-trace cost and latency.
- Open `flows/makerspace-assistant.json` and find the `Language Model` node: it holds the model choice and the `OPENAI_API_KEY` variable name, never the key itself.

## Gotchas we hit

**The traces are in a project called "Langflow", not mine.**
Langflow 1.8 chooses the Opik project from `LANGCHAIN_PROJECT`; `OPIK_PROJECT_NAME`, which its Opik docs mention, is ignored for the trace itself. Start the server with `LANGCHAIN_PROJECT=langflow-makerspace-assistant` (see `demo.py`).

**Only the `llm` span arrives, and the server log says `Error ending trace Prompt Template (...)`.**
Langflow 1.8.4 builds its component spans from the SDK's `SpanData` and passes every field to `Opik.span(...)`. Opik releases from 1.10.55 on added a `source` field that `Opik.span` does not accept, so each component span raises a `TypeError` that Langflow logs and swallows; the trace and the callback's `llm` span still land. 1.10.52 works and 1.10.55 breaks (we tried 1.9.0, 1.10.0, 1.10.40, 1.10.50, 1.10.52, 1.10.55, 1.10.60, 1.11.0, 1.11.6, 1.11.10 and 1.11.14), hence `opik==1.10.52` in `pyproject.toml`. Unpin once Langflow handles `source`.

**`POST /api/v1/run/...` returns 403: "Since v1.5, LANGFLOW_AUTO_LOGIN requires a valid API key".**
Auto-login only covers the UI session. Mint a key with `POST /api/v1/api_key/` (bearer token from `/api/v1/auto_login`) and send it as `x-api-key`, as `demo.py` does.

**Mixed package versions make `langflow run` hang at "Launching Langflow...".**
After probing Opik versions with `uv pip install opik==...`, the server child died on startup and the CLI waited forever with nothing listening on the port. `uv sync` restores a consistent environment.

## How it's put together

- `demo.py` - starts Langflow headless, imports the flow, mints an API key, asks three questions in one session, stops the server. Sets the Opik environment variables Langflow's built-in tracer reads.
- `build_flow.py` - regenerates the flow JSON from Langflow's own "Basic Prompting" starter, pointing it at the guide and gpt-4o-mini.
- `flows/makerspace-assistant.json` - the importable flow (committed, so the demo needs no build step).
- `docs/makerspace-guide.md` - the fictional Quillmere Makerspace member guide: hours, tools and prices, badges, safety rules.
- `pyproject.toml` - Langflow 1.8, the pinned Opik, python-dotenv; `.env.example` - the variables the demo reads.

---

*built with Opik · inspired by Opik's examples and documentation*
