import { Opik, type Trace } from "opik";

import { MODEL, type ChatClient, type ChatMessage } from "./llm.js";

// One Opik client for the whole process. The project name is pinned here so every
// trace lands in the same project; URL, workspace and API key come from the environment.
export const opik = new Opik({ projectName: "opik-ts-translation-pipeline" });

/**
 * A pipeline stage that calls the model, traced by hand: a "general" span for the stage,
 * with the actual completion nested under it as an "llm" span.
 */
export async function tracedChat(
  trace: Trace,
  stage: string,
  client: ChatClient,
  messages: ChatMessage[],
) {
  // trace.span() opens a child of the trace; it stays open (and keeps timing) until end().
  const stageSpan = trace.span({
    name: stage,
    type: "general",
    input: { text: messages[messages.length - 1].content },
  });
  // span.span() nests a child under the stage. type "llm" is what gives it the model,
  // token and cost columns in the UI.
  const llmSpan = stageSpan.span({
    name: `chat ${MODEL}`,
    type: "llm",
    input: { messages },
  });
  try {
    const result = await client.chat(messages);
    llmSpan
      .update({
        output: { text: result.text },
        // The raw OpenAI SDK reports nothing to Opik, so we copy model, provider and token
        // counts onto the span ourselves. Without them the cost column stays empty.
        model: result.model,
        provider: "openai",
        usage: result.usage,
      })
      .end();
    stageSpan.update({ output: { text: result.text } }).end();
    return result;
  } catch (error) {
    // errorInfo marks the span (and its trace) as failed in the UI, with the message.
    const e = error instanceof Error ? error : new Error(String(error));
    llmSpan
      .update({ errorInfo: { exceptionType: e.name, message: e.message, traceback: e.stack ?? "" } })
      .end();
    stageSpan.end();
    throw error;
  }
}
