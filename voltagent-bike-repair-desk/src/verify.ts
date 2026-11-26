// Audits the Opik project after a demo run: `npm run verify`.
// Reads back what the OTLP ingestion produced, over Opik's REST API, and
// checks the things the attribute mapping is supposed to deliver.
import "./env.ts";

const base = (process.env.OPIK_URL_OVERRIDE ?? "https://www.comet.com/opik/api").replace(/\/+$/, "");
const project = process.env.OPIK_PROJECT_NAME ?? "voltagent-bike-repair-desk";
const headers: Record<string, string> = {
  "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
  ...(process.env.OPIK_API_KEY ? { Authorization: process.env.OPIK_API_KEY } : {}),
};

type Span = {
  name: string;
  type: string;
  model?: string;
  provider?: string;
  usage?: Record<string, number>;
  total_estimated_cost?: number | null;
  input?: unknown;
  output?: unknown;
};

async function get<T>(path: string, params: Record<string, string>): Promise<T> {
  const res = await fetch(`${base}/v1/private/${path}?${new URLSearchParams(params)}`, { headers });
  if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
  return (await res.json()) as T;
}

const traces = await get<{ content: { id: string }[] }>("traces", { project_name: project, size: "100" });
const spans = (await get<{ content: Span[] }>("spans", { project_name: project, size: "500" })).content;
const llm = spans.filter((s) => s.type === "llm");
const tools = spans.filter((s) => s.type === "tool");

console.log(`project: ${project}`);
console.log(`traces: ${traces.content.length}, spans: ${spans.length} (llm ${llm.length}, tool ${tools.length})`);
console.log("\nllm spans:");
for (const s of llm) {
  console.log(`  ${s.name}  model=${s.model} provider=${s.provider} usage=${JSON.stringify(s.usage)} cost=${s.total_estimated_cost}`);
}
console.log("\ntool spans:");
for (const s of tools) {
  console.log(`  ${s.name}  input=${JSON.stringify(s.input)?.slice(0, 80)}`);
}

// Each check is the visible symptom of a missing mapping.
const checks: [string, boolean][] = [
  ["at least one trace", traces.content.length > 0],
  ["llm spans exist (typed from gen_ai.request.model)", llm.length > 0],
  ["every llm span has token usage", llm.length > 0 && llm.every((s) => (s.usage?.total_tokens ?? 0) > 0)],
  ["every llm span has a non-null cost", llm.length > 0 && llm.every((s) => (s.total_estimated_cost ?? 0) > 0)],
  ["tool spans exist (typed from gen_ai.tool.*)", tools.length > 0],
  ["every tool span has its arguments as input", tools.length > 0 && tools.every((s) => s.input !== undefined && s.input !== null)],
];
console.log("");
for (const [label, ok] of checks) console.log(`${ok ? "PASS" : "FAIL"}  ${label}`);
process.exit(checks.every(([, ok]) => ok) ? 0 : 1);
