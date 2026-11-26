import { backTranslateMessages, translateMessages } from "./prompts.js";
import type { ChatClient } from "./llm.js";
import { decide, runChecks } from "./qa.js";
import { opik, tracedChat } from "./tracing.js";
import type { Corpus, UiString } from "./types.js";

/** Translate, back-translate, check and decide for one UI string. */
export async function processString(client: ChatClient, corpus: Corpus, item: UiString) {
  // One trace per UI string: the unit a localization reviewer asks about.
  const trace = opik.trace({
    name: "localize-string",
    input: { key: item.key, text: item.text },
    metadata: { targetLanguage: corpus.targetLanguage, app: corpus.app },
  });

  const translation = await tracedChat(trace, "translate", client, translateMessages(corpus, item.text));
  const backTranslation = await tracedChat(
    trace,
    "back-translate",
    client,
    backTranslateMessages(corpus, translation.text),
  );

  // Plain code gets a span too, type "tool", so the checks show up between the model calls
  // with the exact numbers they computed.
  const checkSpan = trace.span({
    name: "quality-checks",
    type: "tool",
    input: { source: item.text, translated: translation.text, backTranslated: backTranslation.text },
  });
  const checks = runChecks(item.text, translation.text, backTranslation.text, corpus.glossary);
  checkSpan.update({ output: checks }).end();

  // "guardrail" is the span type for a pass/block decision; it gets its own badge in the tree.
  const decideSpan = trace.span({ name: "decide", type: "guardrail", input: { checks } });
  const verdict = decide(checks);
  decideSpan.update({ output: verdict }).end();

  // The root output and a tag per verdict make the trace list filterable by pass/review.
  trace.update({ output: { translated: translation.text, ...verdict }, tags: [verdict.verdict] }).end();

  return {
    key: item.key,
    translated: translation.text,
    backTranslated: backTranslation.text,
    checks,
    verdict,
  };
}
