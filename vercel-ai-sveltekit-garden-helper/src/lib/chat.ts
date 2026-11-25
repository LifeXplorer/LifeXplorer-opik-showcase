import { convertToModelMessages, stepCountIs, streamText, type LanguageModel, type UIMessage } from "ai";
import { SYSTEM_PROMPT, plantingCalendar } from "./garden";
import { chatTelemetry } from "./telemetry";

export async function streamGardenReply(model: LanguageModel, chatId: string, messages: UIMessage[]) {
  return streamText({
    model,
    system: SYSTEM_PROMPT,
    messages: await convertToModelMessages(messages),
    tools: { plantingCalendar },
    stopWhen: stepCountIs(4),
    // runtimeContext + telemetry make this call emit the spans that the
    // OpikExporter (src/instrumentation.server.ts) turns into one trace per
    // turn, with the chat id as the thread id.
    ...chatTelemetry(chatId),
  });
}
