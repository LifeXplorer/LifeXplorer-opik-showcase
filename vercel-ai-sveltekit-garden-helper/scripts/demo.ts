// Starts the SvelteKit dev server, plays three scripted garden conversations
// against /api/chat (streaming, two turns each), prints the replies, then
// shuts the server down. No browser and no typing needed.
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import path from "node:path";
import { setTimeout as sleep } from "node:timers/promises";
import { loadEnv } from "../src/lib/server-env";

loadEnv();

const root = process.cwd();
const PORT = process.env.DEMO_PORT ?? "5311";
const BASE = `http://localhost:${PORT}`;

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

const conversations = [
  {
    title: "Tomatoes from seed",
    turns: [
      "When should I sow tomato seeds indoors, and when can the seedlings go out at the Hollyhock Lane plot?",
      "And roughly when will I be picking my first ripe fruit?",
    ],
  },
  {
    title: "Aphids on the kale",
    turns: [
      "The leaves on my kale are curling and covered in tiny green bugs. What should I do?",
      "Will the soap spray you suggested hurt the bees on my sunflowers?",
    ],
  },
  {
    title: "A detour into banking",
    turns: [
      "Can you recommend a good fixed mortgage rate for a first-time buyer?",
      "Fine, back to plants then. How deep should I plant garlic cloves?",
    ],
  },
];

const message = (role: "user" | "assistant", text: string) => ({
  id: randomUUID(),
  role,
  parts: [{ type: "text", text }],
});

type Message = ReturnType<typeof message>;

// POSTs the full history (what the Chat class does) and reads the UI-message
// stream back, printing text deltas as they arrive.
async function chatTurn(chatId: string, messages: Message[]): Promise<string> {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: chatId, messages }),
  });
  if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}: ${await res.text()}`);

  let text = "";
  let buffer = "";
  const decoder = new TextDecoder();
  for await (const chunk of res.body) {
    buffer += decoder.decode(chunk, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ") || line === "data: [DONE]") continue;
      try {
        const event = JSON.parse(line.slice(6));
        if (event.type === "text-delta" && event.delta) {
          text += event.delta;
          process.stdout.write(event.delta);
        }
      } catch {
        /* ignore non-JSON keepalives */
      }
    }
  }
  process.stdout.write("\n");
  return text;
}

async function waitForServer(timeoutMs = 90_000): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(BASE, { signal: AbortSignal.timeout(2000) });
      if (res.ok) return;
    } catch {
      /* not up yet */
    }
    await sleep(500);
  }
  throw new Error("Dev server did not become ready in time");
}

console.log(`Starting the SvelteKit dev server on port ${PORT}...`);
const server = spawn(path.join(root, "node_modules", ".bin", "vite"), ["dev", "--port", PORT, "--strictPort"], {
  cwd: root,
  env: { ...process.env },
  stdio: ["ignore", "pipe", "pipe"],
  detached: true, // own process group so the whole tree can be stopped
});
server.stdout.on("data", () => {});
server.stderr.on("data", (d) => {
  const line = String(d);
  if (/error/i.test(line)) process.stderr.write(line);
});

try {
  await waitForServer();
  console.log("Server is ready.\n");

  for (const conversation of conversations) {
    const chatId = randomUUID();
    console.log(`=== ${conversation.title} (chat ${chatId.slice(0, 8)}) ===`);
    const history: Message[] = [];
    for (const turn of conversation.turns) {
      console.log(`\nYou: ${turn}\nSprout: `);
      history.push(message("user", turn));
      history.push(message("assistant", await chatTurn(chatId, history)));
    }
    console.log();
  }
} finally {
  try {
    if (server.pid) process.kill(-server.pid, "SIGTERM");
  } catch {
    /* already gone */
  }
}
