import { describe, expect, it, vi } from "vitest";
import type { ReadableSpan, SpanExporter } from "@opentelemetry/sdk-trace-base";
import { GenAIExporter, toGenAI } from "../src/genai.ts";

const llmAttrs = {
  "span.type": "llm",
  "llm.model": "gpt-4o-mini",
  "llm.messages": '[{"role":"user","content":"hi"}]',
  "llm.usage.prompt_tokens": 722,
  "llm.usage.completion_tokens": 93,
  "llm.usage.total_tokens": 815,
};

const toolAttrs = {
  "span.type": "tool",
  "tool.name": "repair_status",
  "tool.parameters": '{"_def":{}}',
  input: '{"ticket_id":"RT-2043"}',
  output: '{"status":"ready_for_pickup"}',
};

describe("toGenAI", () => {
  it("maps an llm span to model, provider, usage and prompt", () => {
    const out = toGenAI(llmAttrs, "openai");
    expect(out["gen_ai.request.model"]).toBe("gpt-4o-mini");
    expect(out["gen_ai.provider.name"]).toBe("openai");
    expect(out["gen_ai.usage.prompt_tokens"]).toBe(722);
    expect(out["gen_ai.usage.completion_tokens"]).toBe(93);
    expect(out["gen_ai.usage.total_tokens"]).toBe(815);
    expect(out["gen_ai.prompt"]).toBe(llmAttrs["llm.messages"]);
  });

  it("moves tool input/output to gen_ai.tool.call.* and drops the schema noise", () => {
    const out = toGenAI(toolAttrs, "openai");
    expect(out["gen_ai.tool.call.arguments"]).toBe('{"ticket_id":"RT-2043"}');
    expect(out["gen_ai.tool.call.result"]).toBe('{"status":"ready_for_pickup"}');
    expect(out["gen_ai.tool.name"]).toBe("repair_status");
    expect(out).not.toHaveProperty("input");
    expect(out).not.toHaveProperty("tool.parameters");
  });

  it("files leftover attributes under gen_ai.agent.* so Opik keeps them out of input", () => {
    const out = toGenAI({ ...toolAttrs, "tool.call.id": "call_1" }, "openai");
    expect(out["gen_ai.agent.tool.call.id"]).toBe("call_1");
    expect(out).not.toHaveProperty("tool.call.id");
  });

  it("maps the agent root span's prompt and answer", () => {
    const out = toGenAI({ input: "hello", output: "bye", "entity.type": "agent" }, "openai");
    expect(out["gen_ai.prompt"]).toBe("hello");
    expect(out["gen_ai.completion"]).toBe("bye");
  });

  it("leaves unrelated spans untouched", () => {
    const other = { foo: "bar" };
    expect(toGenAI(other, "openai")).toEqual(other);
  });
});

describe("GenAIExporter", () => {
  it("renames attributes on the spans it hands to the wrapped exporter", () => {
    const exported: ReadableSpan[][] = [];
    const inner: SpanExporter = {
      export: (spans, cb) => {
        exported.push(spans);
        cb({ code: 0 });
      },
      shutdown: async () => {},
    };
    const span = { attributes: { ...llmAttrs } } as unknown as ReadableSpan;
    const done = vi.fn();
    new GenAIExporter(inner, "openai").export([span], done);
    expect(exported[0][0].attributes["gen_ai.provider.name"]).toBe("openai");
    expect(done).toHaveBeenCalledOnce();
  });
});
