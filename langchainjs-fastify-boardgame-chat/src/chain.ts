import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnableLambda, RunnableSequence } from "@langchain/core/runnables";
import type { Runnable, RunnableConfig } from "@langchain/core/runnables";
import type { BaseLanguageModel } from "@langchain/core/language_models/base";
import { HumanMessage } from "@langchain/core/messages";
import type { BaseMessage } from "@langchain/core/messages";
import { formatShortlist, parseWishes, shortlist } from "./catalog.js";
import type { Game } from "./catalog.js";
import { prompt } from "./prompt.js";
import type { SessionStore } from "./sessions.js";

/** What the first step hands to the prompt. */
interface TurnInput {
  history: BaseMessage[];
  message: string;
  shortlist: string;
}

function sessionIdOf(config?: RunnableConfig): string {
  const id = (config?.configurable as { sessionId?: string } | undefined)?.sessionId;
  if (!id) throw new Error("sessionId missing from the run config");
  return id;
}

/**
 * Steps shared by both chains: load this guest's history, then shortlist games
 * from everything the guest has said so far (so "we're four" in turn 1 still
 * counts in turn 3).
 */
function prepareTurn(store: SessionStore, catalog: Game[]) {
  return RunnableLambda.from((message: string, config?: RunnableConfig): TurnInput => {
    const { history } = store.get(sessionIdOf(config));
    const said = [...history.filter((m) => m instanceof HumanMessage).map((m) => String(m.content)), message];
    const picks = shortlist(catalog, parseWishes(said.join(" \n ")));
    return { history, message, shortlist: formatShortlist(picks) };
  }).withConfig({ runName: "prepare-turn" });
}

/** Chain with a plain-string contract: guest text in, host reply out. */
export function buildChain(
  store: SessionStore,
  catalog: Game[],
  llm: BaseLanguageModel
): Runnable<string, string> {
  return RunnableSequence.from([prepareTurn(store, catalog), prompt, llm, new StringOutputParser()]);
}
