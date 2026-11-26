import type { Corpus } from "./types.js";

export function translateMessages(corpus: Corpus, text: string) {
  const glossary = corpus.glossary.map((g) => `- "${g.source}" -> "${g.target}"`).join("\n");
  return [
    {
      role: "system" as const,
      content: `You localize UI strings for the ${corpus.app} app into ${corpus.targetLanguage}.
Keep every {placeholder} exactly as written. Use this glossary whenever a term appears:
${glossary}
Reply with the translation only.`,
    },
    { role: "user" as const, content: text },
  ];
}

export function backTranslateMessages(corpus: Corpus, text: string) {
  return [
    {
      role: "system" as const,
      content: `Translate this ${corpus.targetLanguage} UI string literally into English.
Keep every {placeholder} exactly as written. Reply with the translation only.`,
    },
    { role: "user" as const, content: text },
  ];
}
