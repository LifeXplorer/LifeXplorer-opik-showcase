import { AIMessage, HumanMessage } from "@langchain/core/messages";
import type { BaseMessage } from "@langchain/core/messages";

/** Per-guest memory: the widget's sessionId maps to the conversation so far. */
export interface Session {
  history: BaseMessage[];
}

export class SessionStore {
  private sessions = new Map<string, Session>();

  get(sessionId: string): Session {
    let session = this.sessions.get(sessionId);
    if (!session) {
      session = { history: [] };
      this.sessions.set(sessionId, session);
    }
    return session;
  }

  record(sessionId: string, message: string, reply: string): void {
    this.get(sessionId).history.push(new HumanMessage(message), new AIMessage(reply));
  }
}
