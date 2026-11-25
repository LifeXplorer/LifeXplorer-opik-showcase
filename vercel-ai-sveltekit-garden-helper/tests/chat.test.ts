import { simulateReadableStream, type UIMessage } from "ai";
import { MockLanguageModelV4 } from "ai/test";
import { describe, expect, it } from "vitest";
import { streamGardenReply } from "../src/lib/chat";

// streamGardenReply carries the telemetry settings, but with no exporter registered
// (and OPIK_TRACK_DISABLE set, the SDK's switch for turning Opik off) they are inert,
// so these tests need no Opik server and no OpenAI key.
process.env.OPIK_TRACK_DISABLE = "true";

const usage = {
  inputTokens: { total: 10, noCache: 10, cacheRead: 0, cacheWrite: 0 },
  outputTokens: { total: 5, text: 5, reasoning: 0 },
};

function fakeModel(reply: string) {
  return new MockLanguageModelV4({
    doStream: async () => ({
      stream: simulateReadableStream({
        chunks: [
          { type: "text-start", id: "t" },
          { type: "text-delta", id: "t", delta: reply },
          { type: "text-end", id: "t" },
          { type: "finish", finishReason: { unified: "stop", raw: "stop" }, usage },
        ],
      }),
    }),
  });
}

describe("streamGardenReply with tracking disabled", () => {
  it("streams the model's text and sends the garden system prompt", async () => {
    const model = fakeModel("Sow in March.");
    const messages: UIMessage[] = [
      { id: "1", role: "user", parts: [{ type: "text", text: "When do I sow tomatoes?" }] },
    ];

    const result = await streamGardenReply(model, "chat-1", messages);

    expect(await result.text).toBe("Sow in March.");
    const prompt = model.doStreamCalls[0].prompt;
    expect(JSON.stringify(prompt)).toContain("Sprout");
    expect(model.doStreamCalls[0].tools?.map((t) => t.name)).toEqual(["plantingCalendar"]);
  });
});
