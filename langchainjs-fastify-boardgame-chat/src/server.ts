import path from "node:path";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";
import { ChatOpenAI } from "@langchain/openai";
import { buildApp } from "./app.js";
import { buildChain, buildEnvelopeChain } from "./chain.js";
import { loadCatalog } from "./catalog.js";
import { SessionStore } from "./sessions.js";
import { flushTraces, handlerFor } from "./tracing.js";

const here = path.dirname(fileURLToPath(import.meta.url));
// This folder's .env first, then the nearest ancestor .env; existing values win.
dotenv.config({ path: path.join(here, "../.env"), quiet: true });
dotenv.config({ path: path.join(here, "../../.env"), quiet: true });

export function createRuntime() {
  const store = new SessionStore();
  const llm = new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0.3 });
  const catalog = loadCatalog();
  const chain = buildChain(store, catalog, llm);
  const envelopeChain = buildEnvelopeChain(store, catalog, llm);
  return { app: buildApp({ store, chain, envelopeChain, callbacksFor: (id) => [handlerFor(id)] }), store };
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  const { app } = createRuntime();
  const port = Number(process.env.PORT ?? 3000);
  await app.listen({ port });
  console.log(`Meeple & Brew widget: http://localhost:${port}`);
  for (const signal of ["SIGINT", "SIGTERM"] as const) {
    process.on(signal, async () => {
      await flushTraces(); // buffered traces are lost on exit unless flushed
      process.exit(0);
    });
  }
}
