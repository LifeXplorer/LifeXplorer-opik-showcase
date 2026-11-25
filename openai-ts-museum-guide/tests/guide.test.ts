import { Opik } from "opik";
import { describe, expect, it, vi } from "vitest";
import { loadCollection } from "../src/collection.js";
import { MuseumGuide, newThreadId, type ChatClient } from "../src/guide.js";

function stubClient(replies: string[]) {
  const create = vi.fn(async () => ({
    choices: [{ message: { content: replies.shift() ?? "" } }],
    usage: { prompt_tokens: 100, completion_tokens: 10, total_tokens: 110 },
  }));
  return { client: { chat: { completions: { create } } } as unknown as ChatClient, create };
}

describe("MuseumGuide (tracking disabled via OPIK_TRACK_DISABLE)", () => {
  it("answers through the traced client without a server", async () => {
    const { client } = stubClient(["The cuckoo has seventeen birds."]);
    const opik = new Opik({ projectName: "test" });
    const guide = new MuseumGuide("t1", loadCollection(), client, opik);

    const reply = await guide.answer("How many birds does the cuckoo clock have?");

    expect(reply.text).toBe("The cuckoo has seventeen birds.");
    expect(reply.traceId).toBeTruthy();
    expect(reply.promptTokens).toBe(100);
    expect(guide.turns).toBe(1);
  });

  it("re-sends earlier turns and puts matched exhibits in the system prompt", async () => {
    const { client, create } = stubClient(["First.", "Second."]);
    const guide = new MuseumGuide("t2", loadCollection(), client, new Opik({ projectName: "test" }));

    await guide.answer("Tell me about the orrery");
    await guide.answer("And what time do you close?");

    const calls = create.mock.calls as unknown as Array<[{ messages: Array<{ role: string; content: string }> }]>;
    const secondCall = calls[1]![0].messages;
    expect(secondCall.map((m) => m.role)).toEqual(["system", "user", "assistant", "user"]);
    expect(secondCall[1]?.content).toBe("Tell me about the orrery");
    const firstSystem = calls[0]![0].messages[0]!.content;
    expect(firstSystem).toContain("The Marlow Orrery");
  });
});

describe("newThreadId", () => {
  it("keeps the label but never repeats, so re-runs start fresh threads", () => {
    const a = newThreadId("family-visit");
    const b = newThreadId("family-visit");
    expect(a).toMatch(/^family-visit-[0-9a-f]{8}$/);
    expect(a).not.toBe(b);
  });
});
