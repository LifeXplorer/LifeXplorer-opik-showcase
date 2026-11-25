import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export interface Exhibit {
  id: string;
  room: string;
  title: string;
  year: number;
  summary: string;
  keywords: string[];
}

export interface Collection {
  museum: string;
  hours: string;
  tickets: string;
  exhibits: Exhibit[];
}

export function loadCollection(): Collection {
  const path = fileURLToPath(new URL("../data/collection.json", import.meta.url));
  return JSON.parse(readFileSync(path, "utf8")) as Collection;
}

function tokenize(text: string): string[] {
  return text.toLowerCase().match(/[a-z0-9-]+/g) ?? [];
}

/** Rank exhibits by how many of their keywords appear in the visitor's message. */
export function findExhibits(query: string, exhibits: Exhibit[], limit = 2): Exhibit[] {
  const words = new Set(tokenize(query));
  return exhibits
    .map((exhibit) => ({
      exhibit,
      score: exhibit.keywords.filter((k) => words.has(k)).length,
    }))
    .filter((hit) => hit.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((hit) => hit.exhibit);
}

/** The system prompt is rebuilt every turn so it carries the exhibits relevant right now. */
export function buildSystemPrompt(collection: Collection, relevant: Exhibit[]): string {
  const context = relevant.length
    ? relevant
        .map((e) => `- ${e.title} (${e.year}, ${e.room}): ${e.summary}`)
        .join("\n")
    : "- (no specific exhibit matched this message)";
  return [
    `You are the visitor guide for ${collection.museum}. Be warm, brief (at most three sentences) and concrete.`,
    `Opening hours: ${collection.hours}`,
    `Tickets: ${collection.tickets}`,
    "Exhibits relevant to the visitor's latest message:",
    context,
    "Only state facts found above. If you do not know, say so and suggest asking at the front desk.",
  ].join("\n");
}
