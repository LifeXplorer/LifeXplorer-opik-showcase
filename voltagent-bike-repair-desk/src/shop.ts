// The shop's fictional back office: repair tickets, a parts shelf and a labor
// rate card. Everything is in memory so the demo needs no database; only the
// LLM call leaves your machine. The functions are pure so the tools stay thin.

export type Ticket = {
  id: string;
  customer: string;
  bike: string;
  status: "checked_in" | "waiting_for_parts" | "in_workshop" | "ready_for_pickup";
  jobs: string[];
  eta: string;
  note?: string;
};

export type Part = {
  sku: string;
  name: string;
  category: "chain" | "tire" | "tube" | "brake" | "cable" | "pedal";
  fits: "road" | "mtb" | "commuter" | "any";
  price_usd: number;
  stock: number;
};

export const TICKETS: Ticket[] = [
  { id: "RT-2043", customer: "Priya Nair", bike: "Orbea Gain e-road", status: "ready_for_pickup", jobs: ["brake-bleed", "wheel-true"], eta: "today, after 14:00" },
  { id: "RT-2051", customer: "Tomas Berg", bike: "Surly Cross-Check commuter", status: "waiting_for_parts", jobs: ["chain-replace", "tire-swap"], eta: "Friday", note: "Rear tire on back-order until Thursday." },
  { id: "RT-2058", customer: "Lena Fischer", bike: "Canyon Grizl gravel", status: "in_workshop", jobs: ["tune-up"], eta: "tomorrow noon" },
];

export const PARTS: Part[] = [
  { sku: "CH-110", name: "Velo 11-speed chain", category: "chain", fits: "road", price_usd: 38, stock: 12 },
  { sku: "CH-108", name: "Velo 8-speed commuter chain", category: "chain", fits: "commuter", price_usd: 19, stock: 20 },
  { sku: "TR-700", name: "Marathon 700x35 commuter tire", category: "tire", fits: "commuter", price_usd: 54, stock: 0 },
  { sku: "TR-701", name: "Roadrunner 700x35 commuter tire", category: "tire", fits: "commuter", price_usd: 41, stock: 9 },
  { sku: "TR-290", name: "Knobby 29x2.3 trail tire", category: "tire", fits: "mtb", price_usd: 62, stock: 6 },
  { sku: "TB-700", name: "700c inner tube, 40 mm valve", category: "tube", fits: "any", price_usd: 8, stock: 40 },
  { sku: "BP-100", name: "Disc brake pads, resin (pair)", category: "brake", fits: "any", price_usd: 24, stock: 15 },
  { sku: "CB-020", name: "Brake cable and housing kit", category: "cable", fits: "any", price_usd: 14, stock: 11 },
];

// Labor is flat-rate per job, in USD.
export const LABOR: Record<string, number> = {
  "tune-up": 85,
  "brake-bleed": 60,
  "wheel-true": 35,
  "tire-swap": 20,
  "chain-replace": 25,
};

export const TAX_RATE = 0.08;

export function lookupTicket(id: string): Ticket | undefined {
  return TICKETS.find((t) => t.id.toLowerCase() === id.trim().toLowerCase());
}

// Keyword match over name and category, optionally narrowed to a bike type.
export function searchParts(query: string, bikeType?: Part["fits"]): Part[] {
  const words = query.toLowerCase().split(/\W+/).filter(Boolean);
  return PARTS.filter((p) => {
    if (bikeType && p.fits !== bikeType && p.fits !== "any") return false;
    const haystack = `${p.name} ${p.category}`.toLowerCase();
    return words.some((w) => haystack.includes(w));
  });
}

export type Quote =
  | {
      lines: { label: string; amount_usd: number }[];
      subtotal_usd: number;
      tax_usd: number;
      total_usd: number;
    }
  | { error: string };

export function buildQuote(partSkus: string[], laborJobs: string[]): Quote {
  const lines: { label: string; amount_usd: number }[] = [];
  for (const sku of partSkus) {
    const part = PARTS.find((p) => p.sku === sku);
    if (!part) return { error: `Unknown part SKU ${sku}` };
    if (part.stock === 0) return { error: `${sku} (${part.name}) is out of stock` };
    lines.push({ label: `${part.name} (${sku})`, amount_usd: part.price_usd });
  }
  for (const job of laborJobs) {
    const rate = LABOR[job];
    if (rate === undefined) return { error: `Unknown labor job ${job}` };
    lines.push({ label: `Labor: ${job}`, amount_usd: rate });
  }
  const subtotal = lines.reduce((sum, l) => sum + l.amount_usd, 0);
  const tax = Math.round(subtotal * TAX_RATE * 100) / 100;
  return { lines, subtotal_usd: subtotal, tax_usd: tax, total_usd: Math.round((subtotal + tax) * 100) / 100 };
}
