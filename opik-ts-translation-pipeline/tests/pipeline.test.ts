import { beforeAll, describe, expect, it } from "vitest";

import type { ChatClient } from "../src/llm.js";
import type { Corpus } from "../src/types.js";

// Opik's documented switch for turning tracking off: with it set, the hand-built traces and
// spans in the pipeline send nothing to the server, so the test needs no Opik instance.
process.env.OPIK_TRACK_DISABLE = "true";

const corpus: Corpus = {
  app: "Tidepool",
  targetLanguage: "German",
  glossary: [{ source: "tide window", target: "Gezeitenfenster" }],
  strings: [],
};

// A stub that "translates" by lookup, so the test needs no provider key.
const replies = ["Dein Gezeitenfenster öffnet um {time}.", "Your tide window opens at {time}."];
const stub: ChatClient = {
  async chat() {
    return {
      text: replies.shift() ?? "",
      model: "stub",
      usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
    };
  },
};

describe("processString with tracking disabled", () => {
  let processString: typeof import("../src/pipeline.js").processString;
  beforeAll(async () => {
    ({ processString } = await import("../src/pipeline.js"));
  });

  it("runs the traced pipeline and returns a verdict", async () => {
    const r = await processString(stub, corpus, { key: "k", text: "Your tide window opens at {time}." });
    expect(r.verdict.verdict).toBe("pass");
    expect(r.translated).toContain("{time}");
  });
});
