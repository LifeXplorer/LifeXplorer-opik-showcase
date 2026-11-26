// The lesson: VoltAgent's OTel attributes are close to, but not, the GenAI
// semantic conventions Opik reads. This file renames them on the way out.
import type { ReadableSpan, SpanExporter } from "@opentelemetry/sdk-trace-base";

type Attrs = Record<string, unknown>;

const USAGE_KEYS = ["prompt_tokens", "completion_tokens", "total_tokens"] as const;

// Heavy attributes VoltAgent records that only duplicate other data.
const DROP = ["tool.parameters", "agent.messages", "agent.messages.ui", "agent.stateSnapshot"];

// Returns a copy of one span's attributes with `gen_ai.*` names added.
// Opik's OTel ingestion keys off these names:
//  - gen_ai.request.model + gen_ai.provider.name make an `llm` span that Opik can price;
//    without a recognized provider the tokens land but total_estimated_cost stays null.
//  - gen_ai.usage.* becomes the span's token usage.
//  - gen_ai.tool.call.arguments / .result become a `tool` span's input and output.
//  - Opik puts every attribute it has no rule for into the span INPUT, so the
//    leftovers are renamed under gen_ai.agent.*, which Opik files as metadata.
export function toGenAI(attrs: Attrs, provider: string): Attrs {
  const out: Attrs = {};
  const consumed = new Set<string>(DROP);
  const type = attrs["span.type"];
  if (type === "llm") {
    out["gen_ai.provider.name"] = provider;
    for (const [from, to] of [
      ["llm.model", "gen_ai.request.model"],
      // The message history VoltAgent records becomes the llm span's input.
      ["llm.messages", "gen_ai.prompt"],
      ...USAGE_KEYS.map((k) => [`llm.usage.${k}`, `gen_ai.usage.${k}`]),
    ]) {
      if (attrs[from] !== undefined) out[to] = attrs[from];
      consumed.add(from);
    }
  } else if (type === "tool") {
    out["gen_ai.tool.call.arguments"] = attrs["input"] ?? "{}";
    if (attrs["output"] !== undefined) out["gen_ai.tool.call.result"] = attrs["output"];
    out["gen_ai.tool.name"] = attrs["tool.name"];
    consumed.add("input").add("output").add("tool.name");
  } else if (attrs["entity.type"] === "agent") {
    // The agent root span: its prompt and answer become the trace's input and output.
    if (attrs["input"] !== undefined) out["gen_ai.prompt"] = attrs["input"];
    if (attrs["output"] !== undefined) out["gen_ai.completion"] = attrs["output"];
    consumed.add("input").add("output");
  } else {
    return { ...attrs };
  }
  for (const [key, value] of Object.entries(attrs)) {
    if (!consumed.has(key)) out[`gen_ai.agent.${key}`] = value;
  }
  return out;
}

// Wraps any exporter so every span is renamed just before it is sent.
export class GenAIExporter implements SpanExporter {
  constructor(
    private readonly inner: SpanExporter,
    private readonly provider: string,
  ) {}

  export(spans: ReadableSpan[], resultCallback: Parameters<SpanExporter["export"]>[1]): void {
    for (const span of spans) {
      // ReadableSpan.attributes is readonly in the types but a plain object at
      // runtime; replacing its keys in place is the only way to rewrite a finished span.
      const attrs = span.attributes as Attrs;
      const mapped = toGenAI(attrs, this.provider);
      for (const key of Object.keys(attrs)) delete attrs[key];
      Object.assign(attrs, mapped);
    }
    this.inner.export(spans, resultCallback);
  }

  shutdown(): Promise<void> {
    return this.inner.shutdown();
  }

  forceFlush(): Promise<void> {
    return this.inner.forceFlush?.() ?? Promise.resolve();
  }
}
