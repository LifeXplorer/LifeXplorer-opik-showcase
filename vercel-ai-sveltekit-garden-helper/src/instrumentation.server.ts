// SvelteKit loads this file once, before any app code, when the server starts.
// It is the whole Opik integration: an OpenTelemetry SDK that exports AI SDK
// spans to Opik, plus the AI SDK's own telemetry switch.
import { OpenTelemetry } from "@ai-sdk/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";
import { registerTelemetry } from "ai";
import { Opik } from "opik";
import { OpikExporter } from "opik-vercel";
import { loadEnv } from "./lib/server-env";
import { PROJECT_NAME, spanAttributes } from "./lib/telemetry";

loadEnv();

const g = globalThis as { __gardenOtel?: NodeSDK };

// Vite re-evaluates modules on change; start the SDK only once per process.
if (!g.__gardenOtel) {
  const sdk = new NodeSDK({
    // OpikExporter turns each AI SDK span tree into an Opik trace with nested
    // llm and tool spans. The Opik client pins the project, so every trace
    // lands in one place; URL and workspace come from the OPIK_* variables.
    traceExporter: new OpikExporter({
      client: new Opik({ projectName: PROJECT_NAME }),
      tags: ["sveltekit", "streaming"],
    }),
  });
  sdk.start();
  g.__gardenOtel = sdk;

  // Ask the SDK to flush queued spans when the server is stopped (the demo
  // also waits a few seconds so the last batch is exported either way).
  process.once("SIGTERM", () => void sdk.shutdown());
}

// AI SDK v7 emits telemetry only after this explicit registration (v4-v6 did
// it automatically). Without it the exporter receives no spans at all.
registerTelemetry(
  new OpenTelemetry({
    usage: true, // token counts on the llm spans, which Opik prices into cost
    // Copies the thread id and trace name from the request's runtimeContext
    // onto span attributes; Opik uses them for the Threads tab and trace name.
    enrichSpan: ({ runtimeContext }) => spanAttributes(runtimeContext),
  }),
);
