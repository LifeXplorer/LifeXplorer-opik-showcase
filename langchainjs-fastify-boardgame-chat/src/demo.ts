/**
 * Plays scripted guest sessions against POST /chat on an in-process server,
 * prints the replies, and exits.
 */
import { createRuntime } from "./server.js";
import { flushTraces, PROJECT_NAME } from "./tracing.js";

const PORT = Number(process.env.PORT ?? 3456);

const CONVERSATIONS: Record<string, string[]> = {
  "guest-birthday-four": [
    "Hi! We're four people and most of us have never played a board game before.",
    "We'd like something under an hour that gets us laughing.",
    "Is there anything where we all work together instead of competing?",
  ],
  "guest-date-night": [
    "It's the two of us tonight, something cozy.",
    "We like puzzles. Anything that's quick?",
    "Great, how long does Fox & Lantern take to learn?",
  ],
};

async function chat(sessionId: string, message: string): Promise<string> {
  const response = await fetch(`http://localhost:${PORT}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sessionId, message }),
  });
  if (!response.ok) throw new Error(`POST /chat failed: ${response.status} ${await response.text()}`);
  return ((await response.json()) as { reply: string }).reply;
}

async function main() {
  const { app } = createRuntime();
  await app.listen({ port: PORT });
  for (const [sessionId, turns] of Object.entries(CONVERSATIONS)) {
    console.log(`\n=== Session: ${sessionId} ===`);
    for (const message of turns) {
      console.log(`\nGuest: ${message}`);
      console.log(`Host:  ${await chat(sessionId, message)}`);
    }
  }
  await flushTraces();
  await app.close();
  console.log(`\nDone. Open the "${PROJECT_NAME}" project in Opik and look at the Threads tab.`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
