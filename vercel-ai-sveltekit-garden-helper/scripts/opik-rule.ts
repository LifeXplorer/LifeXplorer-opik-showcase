// Creates the live online-evaluation rule through Opik's REST API. The rule is
// stored on the Opik project, not in the app: Opik's server runs the judge on
// every new trace, so the app ships no scoring code.
import { PROJECT_NAME } from "../src/lib/telemetry";

export const RULE_NAME = "answered_the_garden_question";

const JUDGE_SYSTEM_PROMPT = `You grade a gardening assistant. The input is the JSON of a
chat request; its last user message is the question being answered. Decide
whether the assistant's reply directly answers that question with concrete
gardening advice or dates. A polite refusal, a redirect to another topic, or a
vague non-answer counts as not answered.`;

// Everything the judge sees, built from the trace's input and output.
const JUDGE_USER_PROMPT = `Chat request: {{input}}

Assistant reply: {{output}}`;

export function rulePayload(projectId: string) {
  return {
    name: RULE_NAME,
    project_ids: [projectId],
    sampling_rate: 1, // score every trace; fine for a demo
    enabled: true,
    action: "evaluator",
    type: "llm_as_judge",
    code: {
      // gpt-4o-mini runs server-side; Opik needs an OpenAI key registered in
      // its provider settings for this to produce scores instead of errors.
      model: { name: "gpt-4o-mini", temperature: 0 },
      messages: [
        { role: "SYSTEM", content: JUDGE_SYSTEM_PROMPT },
        { role: "USER", content: JUDGE_USER_PROMPT },
      ],
      // Maps template variables to trace fields.
      variables: { input: "input", output: "output" },
      // The score name that shows up as a feedback-score column on traces.
      schema: [
        {
          name: "answered",
          type: "BOOLEAN",
          description: "True if the reply directly answers the user's last question with concrete gardening advice.",
        },
      ],
    },
  };
}

function api(path: string, init: RequestInit = {}): Promise<Response> {
  const base = (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api/").replace(/\/+$/, "");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
  };
  if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;
  return fetch(`${base}${path}`, { ...init, headers });
}

async function findProjectId(): Promise<string | undefined> {
  const res = await api(`/v1/private/projects?name=${encodeURIComponent(PROJECT_NAME)}&size=50`);
  if (!res.ok) throw new Error(`Listing projects failed: HTTP ${res.status}`);
  const page = (await res.json()) as { content: { id: string; name: string }[] };
  return page.content.find((p) => p.name === PROJECT_NAME)?.id;
}

// Idempotent: creates the project and rule when missing, reuses them otherwise.
// The rule must exist before the traffic arrives; rules only score new traces.
export async function ensureOnlineRule(): Promise<string> {
  let projectId = await findProjectId();
  if (!projectId) {
    const created = await api("/v1/private/projects", { method: "POST", body: JSON.stringify({ name: PROJECT_NAME }) });
    if (!created.ok) throw new Error(`Creating project failed: HTTP ${created.status} ${await created.text()}`);
    projectId = await findProjectId();
  }
  if (!projectId) throw new Error(`Project ${PROJECT_NAME} not found after creating it`);

  const existing = await api(
    `/v1/private/automations/evaluators?project_id=${projectId}&name=${encodeURIComponent(RULE_NAME)}&size=50`,
  );
  if (!existing.ok) throw new Error(`Listing rules failed: HTTP ${existing.status}`);
  const rules = (await existing.json()) as { content: { name: string }[] };
  if (rules.content.some((r) => r.name === RULE_NAME)) return `Rule ${RULE_NAME} already exists, reusing it.`;

  const res = await api("/v1/private/automations/evaluators", {
    method: "POST",
    body: JSON.stringify(rulePayload(projectId)),
  });
  if (!res.ok) throw new Error(`Creating rule failed: HTTP ${res.status} ${await res.text()}`);
  return `Created online rule ${RULE_NAME} on project ${PROJECT_NAME}.`;
}
