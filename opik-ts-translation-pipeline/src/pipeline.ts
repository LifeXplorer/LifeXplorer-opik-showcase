import { backTranslateMessages, translateMessages } from "./prompts.js";
import type { ChatClient } from "./llm.js";
import { decide, runChecks } from "./qa.js";
import type { Corpus, UiString } from "./types.js";

/** Translate, back-translate, check and decide for one UI string. */
export async function processString(client: ChatClient, corpus: Corpus, item: UiString) {
  const translation = await client.chat(translateMessages(corpus, item.text));
  const backTranslation = await client.chat(backTranslateMessages(corpus, translation.text));
  const checks = runChecks(item.text, translation.text, backTranslation.text, corpus.glossary);
  const verdict = decide(checks);
  return {
    key: item.key,
    translated: translation.text,
    backTranslated: backTranslation.text,
    checks,
    verdict,
  };
}
