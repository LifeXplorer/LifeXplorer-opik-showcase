import { existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { config } from "dotenv";

/** Load the nearest .env, walking up from the working directory (a repo-root .env works too). */
export function loadEnv(): void {
  let dir = process.cwd();
  for (;;) {
    const candidate = join(dir, ".env");
    if (existsSync(candidate)) {
      config({ path: candidate, quiet: true });
      return;
    }
    const parent = dirname(dir);
    if (parent === dir) return;
    dir = parent;
  }
}
