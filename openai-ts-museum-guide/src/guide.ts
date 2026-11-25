import type OpenAI from "openai";
import type { Opik } from "opik";
import { trackOpenAI } from "opik-openai";
import { buildSystemPrompt, findExhibits, type Collection } from "./collection.js";

export const MODEL = "gpt-4o-mini";

type Turn = { role: "user" | "assistant"; content: string };

/** The only slice of the OpenAI client the guide needs, so tests can stub it. */
export interface ChatClient {
  chat: { completions: { create: OpenAI["chat"]["completions"]["create"] } };
}

export interface GuideReply {
  text: string;
  traceId: string;
  promptTokens: number;
  completionTokens: number;
}

/** One instance per visitor conversation; it keeps the message history. */
export class MuseumGuide {
  private history: Turn[] = [];

  constructor(
    readonly conversationId: string,
    private readonly collection: Collection,
    private readonly client: ChatClient,
    private readonly opik: Opik,
  ) {}

  get turns(): number {
    return this.history.length / 2;
  }

  async answer(visitorMessage: string): Promise<GuideReply> {
    const relevant = findExhibits(visitorMessage, this.collection.exhibits);
    const system = buildSystemPrompt(this.collection, relevant);
    const turn = this.turns + 1;
    this.history.push({ role: "user", content: visitorMessage });

    // One trace per visitor turn. threadId is what the Threads tab groups on: every turn of
    // this conversation shares it, so the turns read as one transcript instead of loose traces.
    const trace = this.opik.trace({
      name: "guide-turn",
      threadId: this.conversationId,
      input: { visitor_message: visitorMessage },
      metadata: { turn, exhibits: relevant.map((e) => e.id) },
    });

    // trackOpenAI wraps the client with `parent: trace`, so the completion is logged as a child
    // span of this turn's trace (with model, messages and token usage) instead of a trace of its own.
    const traced = trackOpenAI(this.client, {
      client: this.opik,
      parent: trace,
      generationName: "guide-completion",
    });

    try {
      const response = await traced.chat.completions.create({
        model: MODEL,
        messages: [{ role: "system", content: system }, ...this.history],
      });
      const text = response.choices[0]?.message?.content ?? "";
      this.history.push({ role: "assistant", content: text });
      // Thread cards in the UI show the first input and last output, so set the trace output.
      trace.update({ output: { reply: text } });
      return {
        text,
        traceId: trace.data.id,
        promptTokens: response.usage?.prompt_tokens ?? 0,
        completionTokens: response.usage?.completion_tokens ?? 0,
      };
    } finally {
      trace.end();
    }
  }
}
