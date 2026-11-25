import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Fastify from "fastify";
import type { FastifyInstance } from "fastify";
import type { Runnable } from "@langchain/core/runnables";
import type { Callbacks } from "@langchain/core/callbacks/manager";
import type { SessionStore } from "./sessions.js";

const here = path.dirname(fileURLToPath(import.meta.url));

export interface AppDeps {
  store: SessionStore;
  chain: Runnable<string, string>;
  /** Optional per-session callbacks (the Opik handler in the real server). */
  callbacksFor?: (sessionId: string) => Callbacks;
}

/** Build the Fastify app. Dependencies are injected so tests can stub the model. */
export function buildApp({ store, chain, callbacksFor }: AppDeps): FastifyInstance {
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

  return app;
}
