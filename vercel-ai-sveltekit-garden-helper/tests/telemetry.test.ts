import { describe, expect, it } from "vitest";
import { RULE_NAME, rulePayload } from "../scripts/opik-rule";
import { TRACE_NAME, chatTelemetry, spanAttributes } from "../src/lib/telemetry";

describe("telemetry helpers", () => {
  it("maps the runtime context onto the attributes opik-vercel reads", () => {
    expect(spanAttributes({ threadId: "chat-1", traceName: "garden-chat-turn" })).toEqual({
      "ai.telemetry.metadata.threadId": "chat-1",
      "ai.telemetry.metadata.traceName": "garden-chat-turn",
    });
    expect(spanAttributes(undefined)).toEqual({});
  });

  it("uses the chat id as the thread id and opts the context in", () => {
    const settings = chatTelemetry("chat-42");
    expect(settings.runtimeContext).toEqual({ threadId: "chat-42", traceName: TRACE_NAME });
    // Without includeRuntimeContext the AI SDK withholds the context from enrichSpan.
    expect(settings.telemetry.includeRuntimeContext).toEqual({ threadId: true, traceName: true });
  });
});

describe("online rule payload", () => {
  it("scores input and output with a boolean judge on the given project", () => {
    const rule = rulePayload("project-123");
    expect(rule).toMatchObject({ name: RULE_NAME, project_ids: ["project-123"], enabled: true, sampling_rate: 1 });
    expect(rule.code.variables).toEqual({ input: "input", output: "output" });
    expect(rule.code.schema[0]).toMatchObject({ name: "answered", type: "BOOLEAN" });
    expect(rule.code.messages[1].content).toContain("{{input}}");
  });
});
