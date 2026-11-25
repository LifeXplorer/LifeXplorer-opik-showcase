import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["tests/**/*.test.ts"],
    // Tracking off + no provider keys: the suite must pass offline and never touch Opik.
    env: { OPIK_TRACK_DISABLE: "true", OPENAI_API_KEY: "" },
  },
});
