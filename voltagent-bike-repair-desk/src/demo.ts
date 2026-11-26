// Three scripted customer requests through the front-desk agent: `npm run demo`.
// Each request becomes one trace in the Opik project named after this folder.
import "./env.ts";

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

// VoltAgent puts the system prompt inside the messages array, so the AI SDK
// warns on every call; that layout is VoltAgent's, so filter that one warning.
const realWarn = console.warn.bind(console);
console.warn = (...args: unknown[]) => {
  if (typeof args[0] === "string" && args[0].includes("System messages in the prompt")) return;
  realWarn(...args);
};

const { VoltAgent } = await import("@voltagent/core");
const { frontDesk } = await import("./agent.ts");
const { observability, PROJECT } = await import("./observability.ts");

// Passing `observability` hands VoltAgent the Opik-bound tracer: every agent
// call becomes a trace. No `server` means no HTTP server; this stays a script.
new VoltAgent({ agents: { frontDesk }, observability });

const REQUESTS = [
  // 1. One tool: repair_status.
  "Hi, is my bike ready? The ticket is RT-2043 and I'm Priya.",
  // 2. Chains tools: find_parts for the chain and a tire, then quote_repair.
  "My commuter needs a new chain and a rear tire swapped. What parts would you use, and what would it cost me all-in?",
  // 3. Status plus a stock problem: RT-2051 is waiting on a tire that is sold out.
  "Ticket RT-2051: why is it still waiting, and is there a tire I could use instead so I can ride this weekend?",
];

for (const [i, request] of REQUESTS.entries()) {
  console.log(`\n=== Request ${i + 1} ===`);
  console.log(`Customer:  ${request}`);
  const result = await frontDesk.generateText(request);
  console.log(`Assistant: ${result.text}`);
}

// Flush the batch exporter so the last spans reach Opik before the process exits.
await observability.shutdown();
console.log(`\nDone. Open the "${PROJECT}" project in Opik to see the traces.`);
process.exit(0);
