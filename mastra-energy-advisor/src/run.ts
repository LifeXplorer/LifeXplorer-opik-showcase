// `npm run demo`: asks the advisor three questions, each one agent loop (one Opik trace each).
import { config } from "dotenv";
import { fileURLToPath } from "node:url";
import { QUESTIONS } from "./questions.ts";

// Example's .env first, then the repo-root .env.
config({
  path: [fileURLToPath(new URL("../.env", import.meta.url)), fileURLToPath(new URL("../../.env", import.meta.url))],
  quiet: true,
});

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

const { mastra } = await import("./mastra.ts");
const advisor = mastra.getAgent("energyAdvisor");

for (const [i, question] of QUESTIONS.entries()) {
  console.log(`\n=== Question ${i + 1} ===\nHousehold: ${question}`);
  const result = await advisor.generate(question, { maxSteps: 6 });
  console.log(`Wattle:    ${result.text}`);
}

// shutdown() flushes the OTel exporter; without it the last spans never reach Opik.
await mastra.shutdown();
console.log('\nDone. Open the "mastra-energy-advisor" project in Opik to see the traces.');
