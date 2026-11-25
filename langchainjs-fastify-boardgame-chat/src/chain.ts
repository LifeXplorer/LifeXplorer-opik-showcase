import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnableLambda, RunnableSequence } from "@langchain/core/runnables";
import type { Runnable, RunnableConfig } from "@langchain/core/runnables";
import type { BaseLanguageModel } from "@langchain/core/language_models/base";
import { HumanMessage } from "@langchain/core/messages";
import type { BaseMessage } from "@langchain/core/messages";
import { formatShortlist, mentionedGames, parseWishes, shortlist } from "./catalog.js";
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
    const ranked = shortlist(catalog, parseWishes(said.join(" \n ")));
    // Keep every game already named in the conversation (guest or host), so "which of
    // those is quickest?" is answered from catalog facts instead of invented ones.
    const named = mentionedGames(catalog, [...history.map((m) => String(m.content)), message].join(" \n "));
    const picks = [...named, ...ranked.filter((g) => !named.includes(g))].slice(0, 6);
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

/** What the "envelope" variant takes in and hands back. */
export interface Envelope {
  message: string;
  sessionId: string;
}
export interface EnvelopeReply {
  reply: string;
  sessionId: string;
}

/**
 * The same host, but wrapped the way many widget backends are: an object in, an object
 * out. It exists to be compared with buildChain in Opik's Threads tab, where this root
 * run's input and output are JSON envelopes instead of sentences.
 */
export function buildEnvelopeChain(
  store: SessionStore,
  catalog: Game[],
  llm: BaseLanguageModel
): Runnable<Envelope, EnvelopeReply> {
  const unwrap = RunnableLambda.from((env: Envelope) => env.message).withConfig({ runName: "unwrap-envelope" });
  const wrap = RunnableLambda.from(
    (reply: string, config?: RunnableConfig): EnvelopeReply => ({ reply, sessionId: sessionIdOf(config) })
  ).withConfig({ runName: "wrap-envelope" });
  return RunnableSequence.from([unwrap, prepareTurn(store, catalog), prompt, llm, new StringOutputParser(), wrap]);
}
