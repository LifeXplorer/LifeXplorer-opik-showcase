// Pure helpers that decide what the AI SDK telemetry spans carry for Opik.

// Every trace from this app lands in this Opik project.
export const PROJECT_NAME = "vercel-ai-sveltekit-garden-helper";
export const TRACE_NAME = "garden-chat-turn";

// Turns the per-request runtime context into the span attributes opik-vercel
// reads: `ai.telemetry.metadata.threadId` groups turns into one Opik thread,
// and `ai.telemetry.metadata.traceName` names the trace in the traces table.
export function spanAttributes(runtimeContext: Record<string, unknown> | undefined): Record<string, string> {
  const attributes: Record<string, string> = {};
  if (runtimeContext?.threadId != null) {
    attributes["ai.telemetry.metadata.threadId"] = String(runtimeContext.threadId);
  }
  if (runtimeContext?.traceName != null) {
    attributes["ai.telemetry.metadata.traceName"] = String(runtimeContext.traceName);
  }
  return attributes;
}

// Per-request settings for streamText. The chat id from the browser becomes the
// Opik thread id, so every turn of one conversation lands in the same thread.
export function chatTelemetry(chatId: string) {
  return {
    runtimeContext: { threadId: chatId, traceName: TRACE_NAME },
    telemetry: {
      isEnabled: true,
      functionId: TRACE_NAME,
      includeRuntimeContext: { threadId: true, traceName: true },
    },
  };
}
