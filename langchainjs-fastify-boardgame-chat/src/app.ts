import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Fastify from "fastify";
import type { FastifyInstance } from "fastify";
import type { Runnable } from "@langchain/core/runnables";
import type { Callbacks } from "@langchain/core/callbacks/manager";
import type { Envelope, EnvelopeReply } from "./chain.js";
import type { SessionStore } from "./sessions.js";

const here = path.dirname(fileURLToPath(import.meta.url));

export interface AppDeps {
  store: SessionStore;
  chain: Runnable<string, string>;
  /** Optional per-session callbacks (the Opik handler in the real server). */
  /** Object-in, object-out twin of `chain`, served at /chat-envelope for comparison. */
  envelopeChain?: Runnable<Envelope, EnvelopeReply>;
  callbacksFor?: (sessionId: string) => Callbacks;
}

/** Build the Fastify app. Dependencies are injected so tests can stub the model. */
export function buildApp({ store, chain, envelopeChain, callbacksFor }: AppDeps): FastifyInstance {
  const app = Fastify();
  const widget = readFileSync(path.join(here, "../public/index.html"), "utf8");

  app.get("/", async (_req, reply) => reply.type("text/html").send(widget));

  app.post<{ Body: { message?: unknown; sessionId?: unknown } }>("/chat", async (req, reply) => {
    const { message, sessionId } = req.body ?? {};
    if (typeof message !== "string" || !message.trim() || typeof sessionId !== "string" || !sessionId) {
      return reply.code(400).send({ error: "Body must be { message: string, sessionId: string }" });
    }
    try {
      const answer = await chain.invoke(message, {
        runName: "cafe-widget-turn",
        callbacks: callbacksFor?.(sessionId),
        configurable: { sessionId },
      });
      store.record(sessionId, message, answer);
      return { reply: answer, sessionId };
    } catch (error) {
      req.log.error(error);
      return reply.code(500).send({ error: "The host could not answer. Try again." });
    }
  });

  app.post<{ Body: { message?: unknown; sessionId?: unknown } }>("/chat-envelope", async (req, reply) => {
    const { message, sessionId } = req.body ?? {};
    if (!envelopeChain) return reply.code(404).send({ error: "Envelope chain not enabled" });
    if (typeof message !== "string" || !message.trim() || typeof sessionId !== "string" || !sessionId) {
      return reply.code(400).send({ error: "Body must be { message: string, sessionId: string }" });
    }
    try {
      const out = await envelopeChain.invoke(
        { message, sessionId },
        { runName: "cafe-widget-turn", callbacks: callbacksFor?.(sessionId), configurable: { sessionId } }
      );
      store.record(sessionId, message, out.reply);
      return out;
    } catch (error) {
      req.log.error(error);
      return reply.code(500).send({ error: "The host could not answer. Try again." });
    }
  });

  return app;
}
