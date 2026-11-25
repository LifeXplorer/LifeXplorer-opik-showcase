// Reads the project back from Opik's REST API: traces, their spans, threads,
// and the scores the online rule attached. Run it after `npm run demo`.
import { loadEnv } from "../src/lib/server-env";
import { PROJECT_NAME } from "../src/lib/telemetry";

loadEnv();

const base = (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api/").replace(/\/+$/, "");
const headers: Record<string, string> = { "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default" };
if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${base}${path}`, { headers });
  if (!res.ok) throw new Error(`GET ${path} -> HTTP ${res.status}`);
  return (await res.json()) as T;
}

interface Trace {
  id: string;
  name: string;
  thread_id?: string;
  usage?: Record<string, number>;
  total_estimated_cost?: number;
  feedback_scores?: { name: string; value: number; reason?: string }[];
  input?: unknown;
}

const name = encodeURIComponent(PROJECT_NAME);
const { content: all } = await get<{ content: Trace[] }>(`/v1/private/traces?project_name=${name}&size=100`);
// The online rule's own judge calls are logged as `online_evaluation` traces in the same project.
const traces = all.filter((t) => t.name !== "online_evaluation");
console.log(`project ${PROJECT_NAME}: ${traces.length} chat traces (+ ${all.length - traces.length} judge traces)`);

for (const t of [...traces].reverse()) {
  const { content: spans } = await get<{ content: { type: string; name: string }[] }>(
    `/v1/private/spans?project_name=${name}&trace_id=${t.id}&size=100`,
  );
  const shape = spans.map((s) => `${s.type}:${s.name}`).join(", ");
  const scores = (t.feedback_scores ?? []).map((s) => `${s.name}=${s.value}`).join(" ") || "no score yet";
  console.log(
    `- ${t.name} thread=${(t.thread_id ?? "-").slice(0, 8)} tokens=${t.usage?.total_tokens ?? "-"} ` +
      `cost=${t.total_estimated_cost?.toFixed(6) ?? "null"} scores=[${scores}]\n    spans: ${shape}`,
  );
}

const { content: threads } = await get<{ content: { id: string; number_of_messages: number }[] }>(
  `/v1/private/traces/threads?project_name=${name}&size=100`,
);
console.log(`threads: ${threads.length}`);
for (const th of threads) console.log(`- thread ${th.id.slice(0, 8)}: ${th.number_of_messages} messages`);
