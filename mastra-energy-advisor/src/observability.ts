// All of the Opik wiring lives here. Agent and tool files never mention tracing.
import { Observability } from "@mastra/observability";
import { OtelExporter } from "@mastra/otel-exporter";

export const PROJECT_NAME = process.env.OPIK_PROJECT_NAME ?? "mastra-energy-advisor";

// OPIK_TRACK_DISABLE=true returns undefined, so Mastra runs with no exporter: used by offline tests.
export function buildObservability() {
  if (process.env.OPIK_TRACK_DISABLE === "true") return undefined;

  // Opik ingests OpenTelemetry at /v1/private/otel. Default is Opik Cloud; point OPIK_URL_OVERRIDE
  // at e.g. http://localhost:5173/api for a self-hosted stack.
  const base = (process.env.OPIK_URL_OVERRIDE ?? "https://www.comet.com/opik/api").replace(/\/+$/, "");

  // Authorization is only sent when a key exists: self-hosted Opik needs no key.
  const headers: Record<string, string> = {
    "Comet-Workspace": process.env.OPIK_WORKSPACE_NAME ?? process.env.OPIK_WORKSPACE ?? "default",
    // projectName routes every trace into this Opik project instead of "Default Project".
    projectName: PROJECT_NAME,
  };
  if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;

  return new Observability({
    configs: {
      default: {
        serviceName: PROJECT_NAME,
        exporters: [
          // OtelExporter turns each agent run into OTel spans (invoke_agent > agent_step > chat /
          // execute_tool) and posts them to Opik, which renders them as a trace tree.
          // Protobuf, not JSON: the local Opik answers the JSON encoding with "Bad Request".
          // OTEL_DEBUG=1 prints each export result, the only place a failed export is visible.
          new OtelExporter({
            logLevel: process.env.OTEL_DEBUG ? "debug" : undefined,
            provider: { custom: { endpoint: `${base}/v1/private/otel/v1/traces`, protocol: "http/protobuf", headers } },
          }),
        ],
      },
    },
  });
}
