import { defineConfig } from "vitest/config";

// Separate from vite.config.ts so the tests don't load the SvelteKit plugin.
export default defineConfig({
  test: { include: ["tests/**/*.test.ts"], environment: "node" },
});
