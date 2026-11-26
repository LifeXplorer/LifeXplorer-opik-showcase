// The only file that knows tracing exists. VoltAgent's observability layer is
// OpenTelemetry underneath, so an OTLP exporter aimed at Opik's OTel endpoint
// is the whole integration; agent.ts and tools.ts never mention tracing.
import { VoltAgentObservability } from "@voltagent/core";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import type { SpanProcessor } from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-proto";
import { GenAIExporter } from "./genai.ts";
import { MODEL } from "./agent.ts";

export const PROJECT = process.env.OPIK_PROJECT_NAME ?? "voltagent-bike-repair-desk";

// OPIK_TRACK_DISABLE=true is the switch for offline runs and unit tests: no
// span processor means no exporter, so nothing is sent and nothing needs Opik.
export const trackingDisabled = process.env.OPIK_TRACK_DISABLE === "true";

function opikExporter(): OTLPTraceExporter {
  const base = (process.env.OPIK_URL_OVERRIDE ?? "https://www.comet.com/opik/api").replace(/\/+$/, "");
  return new OTLPTraceExporter({
    // Opik's OTLP ingestion path. Protobuf (not http/json) is the encoding this example was verified with.
    url: `${base}/v1/private/otel/v1/traces`,
    headers: {
      // Comet-Workspace picks the workspace and projectName picks the Opik
      // project the traces land in; the Authorization header only matters on Opik Cloud.
      "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
      projectName: PROJECT,
      ...(process.env.OPIK_API_KEY ? { Authorization: process.env.OPIK_API_KEY } : {}),
    },
  });
}

// OPIK_RAW_ATTRS=true skips the rename so you can see what Opik shows for
// VoltAgent's unmapped attributes (untyped spans, no usage, no cost).
const rawAttrs = process.env.OPIK_RAW_ATTRS === "true";

export function buildSpanProcessors(): SpanProcessor[] {
  if (trackingDisabled) return [];
  const exporter = rawAttrs ? opikExporter() : new GenAIExporter(opikExporter(), MODEL.split("/")[0]);
  // Batching exports spans in the background; observability.shutdown() must
  // run before exit or the last spans never reach Opik.
  return [new BatchSpanProcessor(exporter)];
}

export const observability = new VoltAgentObservability({
  serviceName: PROJECT,
  spanProcessors: buildSpanProcessors(),
});
