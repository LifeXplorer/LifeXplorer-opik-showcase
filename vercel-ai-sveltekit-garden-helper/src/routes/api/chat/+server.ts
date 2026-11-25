import { openai } from "@ai-sdk/openai";
import type { UIMessage } from "ai";
import { streamGardenReply } from "../../../lib/chat";
import { loadEnv } from "../../../lib/server-env";
import type { RequestHandler } from "./$types";

loadEnv();

export const POST: RequestHandler = async ({ request }) => {
  // The Chat class sends the chat id and the full message history on every turn.
  const { id, messages }: { id: string; messages: UIMessage[] } = await request.json();

  const result = await streamGardenReply(openai("gpt-4o-mini"), id, messages);
  return result.toUIMessageStreamResponse();
};
