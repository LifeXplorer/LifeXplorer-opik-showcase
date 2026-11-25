import { config } from "dotenv";
import path from "node:path";

// Keys live in one .env shared by the examples in this repo. Load this folder's
// .env and the parent's; neither overrides variables already set in the shell.
export function loadEnv(cwd = process.cwd()): void {
  config({ path: path.resolve(cwd, ".env"), quiet: true });
  config({ path: path.resolve(cwd, "../.env"), quiet: true });
}
