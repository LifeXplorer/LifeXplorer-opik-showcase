# n8n-foodbank-volunteer-screening

*Harvest Table's volunteer sign-up screening, built on the n8n canvas and fully traced in Opik without a single line of instrumentation.*

![n8n](https://img.shields.io/badge/n8n-2.41.7-ea4b71) ![model](https://img.shields.io/badge/model-gpt--4o--mini-10a37f) ![Opik](https://img.shields.io/badge/Opik-OTLP%20hooks-2496ed) ![setup](https://img.shields.io/badge/setup-docker%20compose-blue)

A neighbourhood food bank gets sign-ups all week: someone who has lifted pallets for years, a fifteen-year-old scout who "could drive deliveries", an influencer who wants a fee to film a handout. A coordinator used to read each one. Here a workflow does the first pass, and the interesting question becomes: when it says "decline" or "follow up", what exactly did the model see and say? A canvas workflow has no logging of its own. This example shows how to get that answer from Opik by only adding a package to the Docker image.

## What you'll build

- A self-hosted n8n with a four-node workflow: **Sign-up webhook, Screen volunteer (gpt-4o-mini), Shape the answer, Reply**. POST `name`, `age`, `availability`, `note`; the model answers with `decision` (accept / follow_up / decline), a `role` (sorting, packing, driver, front_desk), a one-sentence `reason` and a `welcome_note`.
- The workflow is a JSON file imported through n8n's public API by `setup.sh`: owner claim, API key, OpenAI credential (from your environment, never from a file), import, activate. No browser involved.
- The Docker image installs [`n8n-observability`](https://github.com/comet-ml/n8n-observability) and points `EXTERNAL_HOOK_FILES` at its hooks, so n8n exports OpenTelemetry spans to Opik's OTLP endpoint. The workflow never mentions Opik.

## See it in Opik

Open the `n8n-foodbank-volunteer-screening` project in Opik (workspace `default` locally). After `./demo.sh` the Traces tab holds three traces, all named **Volunteer screening**, one per sign-up. Each has five spans, and every one is typed `general`:

- `Volunteer screening` (the workflow execution, root)
- `Sign-up webhook`
- `Screen volunteer (gpt-4o-mini)`
- `Shape the answer`
- `Reply`

Click a trace and then the `Screen volunteer (gpt-4o-mini)` span. n8n's node details arrive as flat attributes, and Opik shows them in the span **Input**: `n8n.node.input` (the sign-up JSON the node received), `n8n.node.output` (the model's JSON verdict), and `n8n.node.parameters.messages.values.0.content` / `.1.content` (the system prompt and the user-message template). So when Jonas Berg comes back as *follow_up / packing* ("underage for sorting and needs a guardian to pack"), you can read the exact prompt that produced it. The root span adds `n8n.workflow.id` and `n8n.workflow.name`; the span metadata only says `integration`.

What you will **not** see, and it is worth knowing before you go looking: the trace **Output** is empty (the trace carries its input only), span Output fields are empty (results live in `n8n.node.output` inside Input), and there is no token usage, model name or cost column. With `n8n-observability` 1.0.3 and the OpenAI node used here, the hooks export "n8n spans only" and no `gen_ai.*` attributes are attached to any span. That is the trade of zero-code tracing: complete I/O for every node, no LLM accounting.

## Run it yourself

1. Have Opik running locally (UI at http://localhost:5173) or point the stack at Opik Cloud (see `.env.example`).
2. Put `OPENAI_API_KEY` in a `.env` above this folder, or export it.
3. `./setup.sh` builds the image, starts n8n on http://localhost:5680 and imports the workflow.
4. `./demo.sh` sends three sign-ups, prints the answers, and calls `./check_traces.sh` to wait for the traces and list their spans.
5. Open the `n8n-foodbank-volunteer-screening` project in Opik.
6. `./teardown.sh` when finished (removes the container and its data volume).

## Poke around

- **Add a second Jonas.** Send the scout again with `"age": 19` and a licence mentioned in the note, then compare the two `Screen volunteer` spans: the prompt is identical, only `n8n.node.input` differs.
- **Edit the prompt on the canvas.** Log in at http://localhost:5680 (`volunteers@example.com` / `Foodbank-demo-1`), change a role rule in the OpenAI node, re-send the sign-ups and diff the `messages.values.0.content` attribute across traces.
- **Break an expression.** Rename `$json.message.content.decision` in the Set node to something wrong and send a sign-up: the `Shape the answer` span shows what went in and what came out, so you can see where the field vanished.
- **Send it to Opik Cloud.** Set `OPIK_OTEL_ENDPOINT` and `OPIK_OTEL_HEADERS` as described in `.env.example`, re-run `./setup.sh`, and the same traces appear in the cloud project.


## Gotchas we hit

### The trace check says "found 0" although the traces are in Opik
On macOS the system bash is 3.2, and with `set -u` expanding an empty array (`"${AUTH[@]}"`) aborts with "unbound variable". If that error is swallowed by `2>/dev/null || echo 0`, the poll just reports zero traces. `check_traces.sh` therefore builds its curl call with an `if` on `OPIK_API_KEY` instead of an optional-argument array. Same rule for your own scripts: avoid empty-array expansion under `set -u`.

### The trace has an input but no output, and no cost or tokens
Symptom: Output is blank on the trace and the spans, and the Cost / Usage columns are empty. Cause: `n8n-observability` exports n8n's lifecycle and node data as span attributes, with no `gen_ai.*` fields for the OpenAI node. Fix: read results from `n8n.node.output` in the span Input, or add your own usage logging if you need token accounting; this example deliberately stays zero-code.

## How it's put together

- `Dockerfile` : official n8n image plus `n8n-observability` and the `EXTERNAL_HOOK_FILES` line.
- `docker-compose.yml` : n8n on port 5680, with the OTLP endpoint, workspace header and project name.
- `workflow/volunteer-screening.json` : the exported workflow, credential id replaced by a placeholder.
- `setup.sh` : headless bootstrap through n8n's REST and public APIs.
- `demo.sh` : three fictional sign-ups, then the trace check.
- `check_traces.sh` : polls Opik's REST API until the traces arrive and lists their spans.
- `teardown.sh` : `docker compose down -v`.

---

*built with Opik · inspired by Opik's examples and documentation*
