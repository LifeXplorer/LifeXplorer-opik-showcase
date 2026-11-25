import type OpenAI from "openai";
import { buildSystemPrompt, findExhibits, type Collection } from "./collection.js";

export const MODEL = "gpt-4o-mini";

type Turn = { role: "user" | "assistant"; content: string };

/** The only slice of the OpenAI client the guide needs, so tests can stub it. */
export interface ChatClient {
  chat: { completions: { create: OpenAI["chat"]["completions"]["create"] } };
}

export interface GuideReply {
  text: string;
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
  ) {}

  get turns(): number {
    return this.history.length / 2;
  }

  async answer(visitorMessage: string): Promise<GuideReply> {
    const relevant = findExhibits(visitorMessage, this.collection.exhibits);
    const system = buildSystemPrompt(this.collection, relevant);
    this.history.push({ role: "user", content: visitorMessage });

    const response = await this.client.chat.completions.create({
      model: MODEL,
      messages: [{ role: "system", content: system }, ...this.history],
    });

    const text = response.choices[0]?.message?.content ?? "";
    this.history.push({ role: "assistant", content: text });
    return {
      text,
      promptTokens: response.usage?.prompt_tokens ?? 0,
      completionTokens: response.usage?.completion_tokens ?? 0,
    };
  }
}
