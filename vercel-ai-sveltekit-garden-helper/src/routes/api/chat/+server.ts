import { openai } from "@ai-sdk/openai";
import { convertToModelMessages, stepCountIs, streamText, type UIMessage } from "ai";
import { SYSTEM_PROMPT, plantingCalendar } from "../../../lib/garden";
import { loadEnv } from "../../../lib/server-env";
import type { RequestHandler } from "./$types";

loadEnv();

export const POST: RequestHandler = async ({ request }) => {
  // The Chat class sends the chat id and the full message history on every turn.
  const { messages }: { id: string; messages: UIMessage[] } = await request.json();

  const result = streamText({
    model: openai("gpt-4o-mini"),
    system: SYSTEM_PROMPT,
    messages: await convertToModelMessages(messages),
    tools: { plantingCalendar },
    stopWhen: stepCountIs(4),
  });

  return result.toUIMessageStreamResponse();
};
