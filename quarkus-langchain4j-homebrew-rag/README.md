# quarkus-langchain4j-homebrew-rag

*A Quarkus FAQ bot for a home-brewing club, with every answer traced into Opik straight from the JVM.*

![Java](https://img.shields.io/badge/java-21%2B-ED8B00?logo=openjdk&logoColor=white)
![Quarkus](https://img.shields.io/badge/quarkus-4.0-4695EB?logo=quarkus&logoColor=white)
![LangChain4j](https://img.shields.io/badge/quarkus--langchain4j-OpenAI-1C3C3C)
![Opik](https://img.shields.io/badge/Opik-OTLP-2f54eb)

The Copperkettle Homebrew Club keeps its know-how in four markdown FAQs: mashing, yeast, sanitation,
bottling. A member asks "how much priming sugar for five gallons?" and a small Quarkus service retrieves the
right paragraphs and has `gpt-4o-mini` answer from them. When the bot says something odd, you want to know
whether it fetched the wrong paragraphs or ignored the right ones. There is no Opik SDK for Java here, and
none is needed: Quarkus already speaks OpenTelemetry, and Opik ingests OTLP directly.

## What you'll build

- `GET /ask?q=...` on port 8310, backed by a LangChain4j AI service (`BrewingAssistant`).
- At startup, `docs/*.md` is split into ~450-character chunks, embedded with `text-embedding-3-small` and
  kept in an in-memory embedding store.
- Per question, the three nearest chunks (min score 0.3) are injected into the prompt; the system prompt
  says to answer only from them, or reply "I don't know - ask a club mentor."
- Tracing is configuration only: the `quarkus-opentelemetry` dependency plus a few lines in
  `application.properties`. No Opik code anywhere.
- `run.sh` builds, starts the service, asks four scripted questions (one the FAQ cannot answer: oak barrels
  with Brettanomyces) and shuts down gracefully.

## See it in Opik

Open http://localhost:5173, workspace `default`, project `quarkus-langchain4j-homebrew-rag`. After one run
the Traces tab holds four `GET /ask` traces, one per question, plus a standalone `POST /embeddings` trace
from the startup indexing (the indexer makes two embedding calls; in our run only one showed up as a trace row).

Open a `GET /ask` trace. It has five spans: the server span `GET /ask` at the root, a
`langchain4j.aiservices.BrewingAssistant.answer` span under it, two `POST /embeddings` HTTP client spans, and
`completion gpt-4o-mini`, the only span of type `llm`. That span carries the model
(`gpt-4o-mini-2024-07-18`), provider `openai`, token usage (340 to 403 total tokens per question in our
run) and an estimated cost between $0.00006 and $0.00009. Its Input holds the whole prompt under
`gen_ai.prompt`: system message, the question, then "Answer using the following information:" followed by the
retrieved chunks. Its Output holds `gen_ai.completion`.

The oak-barrel question is the instructive one. Its prompt lists chunks about infection signs and
fermentation temperature: the nearest paragraphs in the corpus, but irrelevant, and the model correctly
replied "I don't know - ask a club mentor." In the priming-sugar trace the chunk with "4.5 ounces (127 grams)"
sits right in the prompt. That is the retrieval-versus-generation split, readable in one span.

## Run it yourself

1. Install JDK 21+ and Maven 3.9+.
2. `cp .env.example .env` and set `OPENAI_API_KEY` (or keep it in a parent-directory `.env`, which `run.sh` also reads).
3. Start a local Opik (default endpoint `http://localhost:5173`).
4. `./run.sh`. It prints each question and answer; the whole run takes about fifteen seconds and well under a cent.

For Opik Cloud, set the full header yourself:
`export QUARKUS_OTEL_EXPORTER_OTLP_TRACES_HEADERS="Authorization=<key>,Comet-Workspace=<workspace>,projectName=quarkus-langchain4j-homebrew-rag"`
and `OPIK_OTLP_ENDPOINT=https://www.comet.com/opik/api/v1/private/otel`.

## Poke around

- Add a fifth question to the heredoc in `run.sh` and find its trace by `url.query` on the server span.
- Set `faq.top-k=1` in `application.properties` and watch the prompt shrink; ask the multi-part sugar question again.
- Raise `faq.min-score` to 0.6 and see which questions now retrieve nothing.
- Flip `include-completion` to `false` and compare the llm span's Output.

## Gotchas we hit

- **The llm span has tokens and cost but empty Input/Output.** Quarkus LangChain4j leaves prompt and completion
  off spans by default. Fix: `quarkus.langchain4j.tracing.include-prompt=true` and
  `quarkus.langchain4j.tracing.include-completion=true`. Prompts then contain your FAQ text, so mind that in production.
- **Warnings about `localhost:4318` and a `NullPointerException` in `BatchLogRecordProcessor` at shutdown.**
  Quarkus 4 also exports logs and metrics, and the defaults point at a collector that isn't there. Fix:
  `quarkus.otel.logs.enabled=false` and `quarkus.otel.metrics.enabled=false`.

- **Traces go missing: only some of the four questions (often none) show up, and the app log says nothing.**
  We watched the exporter through a logging proxy: every batch that left the JVM got HTTP 200, and with the
  default sampler most requests produced nothing to send. Fix: `quarkus.otel.traces.sampler=always_on`; after
  that all four questions arrived on every run. One more
  source of loss: stopping the app right after the last answer dropped that question's trace even with a
  graceful SIGTERM, so `run.sh` sleeps two seconds before stopping it. In your own service the batch
  processor keeps running, so this only matters for short scripted runs.

## How it's put together

- `pom.xml`: Quarkus 4.0.1 platform BOM plus the quarkus-langchain4j BOM; REST, OpenAI and OpenTelemetry extensions.
- `src/main/resources/application.properties`: model names, retrieval knobs and the whole Opik/OTLP wiring.
- `src/main/java/org/copperkettle/faq/BrewingAssistant.java`: the AI service and its system prompt.
- `.../RetrievalConfig.java`: in-memory embedding store and the retrieval augmentor (top-k, min score).
- `.../FaqIngestor.java`: loads, splits and embeds `docs/` at startup.
- `.../AskResource.java`: the `/ask` endpoint.
- `docs/`: the four fictional FAQ files.
- `run.sh`: build, start, ask, stop gracefully so pending spans flush.
- `.env.example`: keys and Opik endpoint settings.

*built with Opik · inspired by Opik's examples and documentation*
