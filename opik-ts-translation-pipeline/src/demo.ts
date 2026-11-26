import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import dotenv from "dotenv";

import { MODEL, openAiClient } from "./llm.js";
import { processString } from "./pipeline.js";
import { opik } from "./tracing.js";
import type { Corpus } from "./types.js";

const here = path.dirname(fileURLToPath(import.meta.url));
// Load the example's .env, then the nearest repo-root .env (existing values win).
dotenv.config({ path: path.join(here, "../.env"), quiet: true });
dotenv.config({ path: path.join(here, "../../.env"), quiet: true });
// A local OpenAI proxy would hide the real API from this example.
delete process.env.OPENAI_BASE_URL;

const corpus = JSON.parse(
  readFileSync(path.join(here, "../data/strings.json"), "utf8"),
) as Corpus;

async function main() {
  console.log(`Checking ${corpus.strings.length} ${corpus.app} strings into ${corpus.targetLanguage} with ${MODEL}...\n`);
  const client = openAiClient();
  for (const item of corpus.strings) {
    const r = await processString(client, corpus, item);
    console.log(`[${r.verdict.verdict.toUpperCase().padEnd(6)}] ${r.key}`);
    console.log(`   ${item.text}\n   ${r.translated}\n   (back) ${r.backTranslated}`);
    if (r.verdict.reasons.length) console.log(`   ${r.verdict.reasons.join(" | ")}`);
  }

  // The SDK sends traces from a background batch queue. A script that exits first drops
  // whatever is still queued, so flush() must be awaited before the process ends.
  await opik.flush();
  console.log('\nDone. Open the "opik-ts-translation-pipeline" project in Opik.');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
