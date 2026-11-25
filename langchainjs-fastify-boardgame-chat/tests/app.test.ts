import { FakeListChatModel } from "@langchain/core/utils/testing";
import { describe, expect, it } from "vitest";
import { buildApp } from "../src/app.js";
import { buildChain, buildEnvelopeChain } from "../src/chain.js";
import { loadCatalog } from "../src/catalog.js";
import { SessionStore } from "../src/sessions.js";

function makeApp(callbacksFor?: Parameters<typeof buildApp>[0]["callbacksFor"]) {
  const store = new SessionStore();
  const catalog = loadCatalog();
  const llm = new FakeListChatModel({ responses: ["Try Saltmarsh Signals.", "It takes about 35 minutes."] });
  const app = buildApp({
    store,
    chain: buildChain(store, catalog, llm),
    envelopeChain: buildEnvelopeChain(store, catalog, llm),
    callbacksFor,
  });
  return { app, store };
}

describe("POST /chat", () => {
  it("answers with a plain string and remembers the turn", async () => {
    const { app, store } = makeApp();
    const res = await app.inject({ method: "POST", url: "/chat", payload: { message: "Four of us, co-op please", sessionId: "s1" } });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toEqual({ reply: "Try Saltmarsh Signals.", sessionId: "s1" });
    expect(store.get("s1").history).toHaveLength(2);
  });

  it("rejects a body without a sessionId", async () => {
    const { app } = makeApp();
    const res = await app.inject({ method: "POST", url: "/chat", payload: { message: "hello" } });
    expect(res.statusCode).toBe(400);
  });

  it("serves the envelope variant with an object reply", async () => {
    const { app } = makeApp();
    const res = await app.inject({ method: "POST", url: "/chat-envelope", payload: { message: "Two of us", sessionId: "s2" } });
    expect(res.json()).toEqual({ reply: "Try Saltmarsh Signals.", sessionId: "s2" });
  });
});

describe("with Opik tracking disabled", () => {
  it("runs a turn through the real Opik callback handler without side effects", async () => {
    // OPIK_TRACK_DISABLE is set by vitest.config.ts, so the handler is a no-op for tracing.
    const { handlerFor } = await import("../src/tracing.js");
    const { app } = makeApp((id) => [handlerFor(id)]);
    const res = await app.inject({ method: "POST", url: "/chat", payload: { message: "Three of us", sessionId: "s3" } });
    expect(res.statusCode).toBe(200);
    expect(res.json().reply).toBe("Try Saltmarsh Signals.");
  });
});
