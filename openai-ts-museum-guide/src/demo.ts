import { createInterface } from "node:readline/promises";
import OpenAI from "openai";
import { Opik } from "opik";
import { loadCollection } from "./collection.js";
import { loadEnv } from "./env.js";
import { MuseumGuide } from "./guide.js";

loadEnv();

const CONVERSATIONS: Record<string, string[]> = {
  "family-visit": [
    "Hi! We're coming with two kids on Saturday. Is there anything they'd enjoy?",
    "How many birds does that cuckoo clock have, and when do they come out?",
    "Lovely. What time do you close, and how much are tickets for two adults and two children aged 7 and 9?",
  ],
  "accessibility-question": [
    "I use a wheelchair. Can I see the big bell in the tower?",
    "Is there anywhere to sit down for lunch afterwards?",
    "Great, and is the orrery in the Pendulum Hall wound by hand?",
  ],
};

const PROJECT = "openai-ts-museum-guide";

// One Opik client for the whole run; projectName decides which project the traces land in.
function createOpik(): Opik {
  return new Opik({ projectName: PROJECT });
}

async function runDemo(opik: Opik): Promise<void> {
  const collection = loadCollection();
  const client = new OpenAI();
  for (const [conversationId, turns] of Object.entries(CONVERSATIONS)) {
    console.log(`\n=== Conversation: ${conversationId} ===`);
    const guide = new MuseumGuide(conversationId, collection, client, opik);
    for (const message of turns) {
      console.log(`\nVisitor: ${message}`);
      const reply = await guide.answer(message);
      console.log(`Guide:   ${reply.text}`);
      console.log(`         (${reply.promptTokens} prompt + ${reply.completionTokens} completion tokens)`);
    }
  }
}

async function runInteractive(opik: Opik): Promise<void> {
  const guide = new MuseumGuide(`interactive-${Date.now().toString(36)}`, loadCollection(), new OpenAI(), opik);
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  console.log("Wrenfield visitor guide. Ctrl+C to quit.");
  try {
    for (;;) {
      const message = (await rl.question("\nYou: ")).trim();
      if (message) console.log(`Guide: ${(await guide.answer(message)).text}`);
    }
  } finally {
    rl.close();
  }
}

const opik = createOpik();
try {
  await (process.argv.includes("--interactive") ? runInteractive(opik) : runDemo(opik));
} finally {
  // Traces are sent in batches; without flush() the process can exit before the last ones leave.
  await opik.flush();
}
