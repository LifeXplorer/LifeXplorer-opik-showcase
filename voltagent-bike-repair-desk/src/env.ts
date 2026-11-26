// Loads the example's .env, falling back to the repo-root .env, and strips a
// local LLM proxy so the demo talks to the public OpenAI API.
import { config } from "dotenv";
import { fileURLToPath } from "node:url";

config({
  path: [
    fileURLToPath(new URL("../.env", import.meta.url)),
    fileURLToPath(new URL("../../.env", import.meta.url)),
  ],
  quiet: true,
});
delete process.env.OPENAI_BASE_URL;
