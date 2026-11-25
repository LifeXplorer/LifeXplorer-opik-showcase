import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export interface Game {
  id: string;
  name: string;
  minPlayers: number;
  maxPlayers: number;
  minutes: number;
  weight: "light" | "medium" | "heavy";
  tags: string[];
  pitch: string;
}

export interface Wishes {
  players?: number;
  maxMinutes?: number;
  weight?: Game["weight"];
  tags: string[];
}

const here = path.dirname(fileURLToPath(import.meta.url));

export function loadCatalog(): Game[] {
  return JSON.parse(readFileSync(path.join(here, "../data/games.json"), "utf8")) as Game[];
}

const NUMBER_WORDS: Record<string, number> = {
  two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8,
};

const TAG_KEYWORDS: Record<string, string[]> = {
  cooperative: ["cooperative", "co-op", "coop", "work together", "teamwork"],
  team: ["team"],
  bluffing: ["bluff", "lying", "traitor", "deception"],
  party: ["party", "loud", "laugh", "silly"],
  cozy: ["cozy", "cosy", "relax", "calm", "gentle"],
  puzzle: ["puzzle", "brain teaser"],
  strategy: ["strategy", "strategic", "crunchy"],
  quick: ["quick", "short", "filler"],
  duel: ["duel", "two-player", "head to head"],
  family: ["family", "kids", "children"],
};

/** Pull party size, time budget, difficulty and mood out of free text. */
export function parseWishes(text: string): Wishes {
  const t = text.toLowerCase();
  const wishes: Wishes = { tags: [] };

  const digits = t.match(/\b(\d+)\s*(?:of us|people|players|friends|adults)\b/);
  const wordy = t.match(/\b(two|three|four|five|six|seven|eight)\s*(?:of us|people|players|friends|adults)\b/);
  const group = t.match(/\b(?:group|party|table) of (\d+)\b/);
  if (digits?.[1]) wishes.players = Number(digits[1]);
  else if (wordy?.[1]) wishes.players = NUMBER_WORDS[wordy[1]];
  else if (group?.[1]) wishes.players = Number(group[1]);

  const minutes = t.match(/\b(\d+)\s*(?:min|minutes)\b/);
  if (minutes?.[1]) wishes.maxMinutes = Number(minutes[1]);
  else if (/under an hour|less than an hour/.test(t)) wishes.maxMinutes = 60;
  else if (/\bquick|short\b/.test(t)) wishes.maxMinutes = 45;

  if (/never played|new to|beginner|easy|simple|first time/.test(t)) wishes.weight = "light";
  else if (/heavy|crunchy|complex|brain burner/.test(t)) wishes.weight = "heavy";

  for (const [tag, words] of Object.entries(TAG_KEYWORDS)) {
    if (words.some((w) => t.includes(w))) wishes.tags.push(tag);
  }
  return wishes;
}

/** Rank the catalog against the wishes and keep the best few for the prompt. */
export function shortlist(games: Game[], wishes: Wishes, limit = 4): Game[] {
  const { players } = wishes;
  const fits = games.filter(
    (g) => players === undefined || (g.minPlayers <= players && players <= g.maxPlayers)
  );
  const score = (g: Game): number => {
    let s = 0;
    if (wishes.maxMinutes !== undefined) s += g.minutes <= wishes.maxMinutes + 10 ? 2 : -2;
    if (wishes.weight) s += g.weight === wishes.weight ? 2 : 0;
    s += g.tags.filter((tag) => wishes.tags.includes(tag)).length;
    return s;
  };
  return fits
    .map((g) => ({ g, s: score(g) }))
    .sort((a, b) => b.s - a.s || a.g.name.localeCompare(b.g.name))
    .slice(0, limit)
    .map((x) => x.g);
}

/** Games whose names appear in the text, so a follow-up like "which of those?" keeps them. */
export function mentionedGames(games: Game[], text: string): Game[] {
  const t = text.toLowerCase().replace(/&/g, "and");
  return games.filter((g) => t.includes(g.name.toLowerCase().replace(/&/g, "and")));
}

export function formatShortlist(games: Game[]): string {
  if (games.length === 0) return "(no game in the library fits that party size)";
  return games
    .map(
      (g) =>
        `- ${g.name} (${g.minPlayers}-${g.maxPlayers} players, ~${g.minutes} min, ${g.weight}): ${g.pitch}`
    )
    .join("\n");
}
