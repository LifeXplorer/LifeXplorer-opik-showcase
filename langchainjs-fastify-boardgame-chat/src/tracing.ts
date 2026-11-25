import { Opik } from "opik";
import { OpikCallbackHandler } from "opik-langchain";

export const PROJECT_NAME = "langchainjs-fastify-boardgame-chat";

// One shared client: it batches every guest's traces over a single connection, and
// projectName makes all of them land in one Opik project instead of "Default Project".
export const opikClient = new Opik({ projectName: PROJECT_NAME });

const handlers = new Map<string, OpikCallbackHandler>();

/**
 * One OpikCallbackHandler per guest session. The handler turns each chain run into a
 * trace with nested spans (LangChain steps, llm span with tokens and cost), and threadId
 * stamps every trace with the guest's sessionId, so Opik's Threads tab groups the turns
 * into one conversation. Without threadId each turn is an unrelated trace.
 */
export function handlerFor(sessionId: string): OpikCallbackHandler {
  let handler = handlers.get(sessionId);
  if (!handler) {
    handler = new OpikCallbackHandler({ client: opikClient, threadId: sessionId });
    handlers.set(sessionId, handler);
  }
  return handler;
}

// Traces are buffered and sent in batches; flushing before exit is what makes the last turns appear.
export async function flushTraces(): Promise<void> {
  await opikClient.flush();
}
