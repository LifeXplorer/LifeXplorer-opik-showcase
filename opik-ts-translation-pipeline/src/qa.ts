import type { CheckResult, GlossaryTerm, Verdict } from "./types.js";

/** Longest a translation may be, relative to the source, before a UI label gets truncated. */
export const MAX_LENGTH_RATIO = 1.6;
/** Minimum word overlap between the source and its back-translation. */
export const MIN_SIMILARITY = 0.45;

const PLACEHOLDER = /\{[a-zA-Z_]+\}/g;

export function placeholdersOf(text: string): string[] {
  return (text.match(PLACEHOLDER) ?? []).sort();
}

export function checkPlaceholders(source: string, translated: string) {
  const want = placeholdersOf(source);
  const got = placeholdersOf(translated);
  const missing = want.filter((p) => !got.includes(p));
  const extra = got.filter((p) => !want.includes(p));
  return { ok: missing.length === 0 && extra.length === 0, missing, extra };
}

/** Every glossary term found in the source must show up in its mandated form. */
export function checkGlossary(
  source: string,
  translated: string,
  glossary: GlossaryTerm[],
) {
  const violations = glossary
    .filter((g) => source.toLowerCase().includes(g.source.toLowerCase()))
    .filter((g) => !translated.toLowerCase().includes(g.target.toLowerCase()))
    .map((g) => `"${g.source}" should be "${g.target}"`);
  return { ok: violations.length === 0, violations };
}

export function checkLength(source: string, translated: string) {
  const ratio = Number((translated.length / source.length).toFixed(2));
  return { ok: ratio <= MAX_LENGTH_RATIO, ratio };
}

function words(text: string): Set<string> {
  return new Set(
    text
      .toLowerCase()
      .replace(PLACEHOLDER, " ")
      .split(/[^a-z0-9]+/)
      .filter((w) => w.length > 2),
  );
}

/** Jaccard overlap of the words in the source and in the round-tripped text. */
export function similarity(source: string, backTranslated: string): number {
  const a = words(source);
  const b = words(backTranslated);
  if (a.size === 0 && b.size === 0) return 1;
  let shared = 0;
  for (const w of a) if (b.has(w)) shared++;
  return Number((shared / (a.size + b.size - shared)).toFixed(2));
}

export function runChecks(
  source: string,
  translated: string,
  backTranslated: string,
  glossary: GlossaryTerm[],
): CheckResult {
  return {
    placeholders: checkPlaceholders(source, translated),
    glossary: checkGlossary(source, translated, glossary),
    length: checkLength(source, translated),
    similarity: similarity(source, backTranslated),
  };
}

export function decide(checks: CheckResult): Verdict {
  const reasons: string[] = [];
  if (!checks.placeholders.ok) {
    reasons.push(
      `placeholders: missing [${checks.placeholders.missing}] extra [${checks.placeholders.extra}]`,
    );
  }
  if (!checks.glossary.ok) reasons.push(`glossary: ${checks.glossary.violations.join("; ")}`);
  if (!checks.length.ok) reasons.push(`length: ${checks.length.ratio}x the source`);
  if (checks.similarity < MIN_SIMILARITY) {
    reasons.push(`back-translation drifted (similarity ${checks.similarity})`);
  }
  return { verdict: reasons.length === 0 ? "pass" : "review", reasons };
}
