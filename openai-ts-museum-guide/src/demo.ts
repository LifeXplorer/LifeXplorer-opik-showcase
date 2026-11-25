import { createInterface } from "node:readline/promises";
import OpenAI from "openai";
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

async function runDemo(): Promise<void> {
  const collection = loadCollection();
  const client = new OpenAI();
  for (const [conversationId, turns] of Object.entries(CONVERSATIONS)) {
    console.log(`\n=== Conversation: ${conversationId} ===`);
    const guide = new MuseumGuide(conversationId, collection, client);
    for (const message of turns) {
      console.log(`\nVisitor: ${message}`);
      const reply = await guide.answer(message);
      console.log(`Guide:   ${reply.text}`);
      console.log(`         (${reply.promptTokens} prompt + ${reply.completionTokens} completion tokens)`);
    }
  }
}

async function runInteractive(): Promise<void> {
  const guide = new MuseumGuide(`interactive-${Date.now().toString(36)}`, loadCollection(), new OpenAI());
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

await (process.argv.includes("--interactive") ? runInteractive() : runDemo());
