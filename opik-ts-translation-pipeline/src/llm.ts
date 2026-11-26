import OpenAI from "openai";

export const MODEL = "gpt-4o-mini";

export interface ChatMessage {
  role: "system" | "user";
  content: string;
}

export interface ChatResult {
  text: string;
  model: string;
  usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
}

export interface ChatClient {
  chat(messages: ChatMessage[]): Promise<ChatResult>;
}

/** A thin wrapper over the plain OpenAI SDK, so the pipeline can be tested with a stub. */
export function openAiClient(): ChatClient {
  const openai = new OpenAI();
  return {
    async chat(messages) {
      const response = await openai.chat.completions.create({
        model: MODEL,
        messages,
        temperature: 0,
      });
      return {
        text: (response.choices[0].message.content ?? "").trim(),
        model: response.model,
        usage: {
          prompt_tokens: response.usage?.prompt_tokens ?? 0,
          completion_tokens: response.usage?.completion_tokens ?? 0,
          total_tokens: response.usage?.total_tokens ?? 0,
        },
      };
    },
  };
}
