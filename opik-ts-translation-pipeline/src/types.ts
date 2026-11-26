export interface GlossaryTerm {
  source: string;
  target: string;
}

export interface UiString {
  key: string;
  text: string;
}

export interface Corpus {
  app: string;
  targetLanguage: string;
  glossary: GlossaryTerm[];
  strings: UiString[];
}

export interface CheckResult {
  placeholders: { ok: boolean; missing: string[]; extra: string[] };
  glossary: { ok: boolean; violations: string[] };
  length: { ok: boolean; ratio: number };
  similarity: number;
}

export interface Verdict {
  verdict: "pass" | "review";
  reasons: string[];
}
