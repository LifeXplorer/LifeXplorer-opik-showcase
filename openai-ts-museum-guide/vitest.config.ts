import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // Opik's documented switch for turning tracking off: nothing is sent, so tests need no server or keys.
    env: { OPIK_TRACK_DISABLE: "true" },
  },
});
