import { Mastra } from "@mastra/core/mastra";
import { PinoLogger } from "@mastra/loggers";
import { LibSQLStore } from "@mastra/libsql";
import { energyAdvisor } from "./agents/advisor.ts";
import { buildObservability } from "./observability.ts";

export const mastra = new Mastra({
  agents: { energyAdvisor },
  storage: new LibSQLStore({ id: "memory-store", url: ":memory:" }),
  logger: new PinoLogger({ name: "Mastra", level: "warn" }),
  // Passing observability here is the whole integration: no tracing calls anywhere else.
  observability: buildObservability(),
});
