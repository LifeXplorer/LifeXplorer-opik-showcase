import { readFileSync } from "node:fs";
import path from "node:path";
import { tool } from "ai";
import { z } from "zod";

export const SYSTEM_PROMPT = `You are Sprout, the garden helper for the Hollyhock Lane Community
Garden, a fictional shared plot in Marrow Valley. You help members with
planting times, watering, pests and bed planning. When someone asks when to
sow, plant out or harvest a crop, call the plantingCalendar tool instead of
guessing dates. Answer in two to four sentences. If a question has nothing to
do with gardening, say so politely and steer back to the garden.`;

export interface Plant {
  name: string;
  sowIndoorsWeeks: number | null; // weeks relative to last frost; negative = before
  transplantWeeks: number; // when to plant out (or direct sow) relative to last frost
  harvestDays: number; // days from planting out to first harvest
  note: string;
}

interface PlantFile {
  garden: string;
  lastFrost: string;
  plants: Plant[];
}

export function loadPlantFile(file = path.resolve(process.cwd(), "data/plants.json")): PlantFile {
  return JSON.parse(readFileSync(file, "utf8")) as PlantFile;
}

const DAY_MS = 24 * 60 * 60 * 1000;

/** Date `weeks` away from `base`, formatted YYYY-MM-DD (UTC, so tests are stable). */
export function shiftWeeks(base: string, weeks: number): string {
  return new Date(new Date(`${base}T00:00:00Z`).getTime() + weeks * 7 * DAY_MS)
    .toISOString()
    .slice(0, 10);
}

export type PlantingResult =
  | {
      found: true;
      plant: string;
      sowIndoors: string | null;
      plantOut: string;
      firstHarvest: string;
      note: string;
    }
  | { found: false; knownPlants: string[] };

export function planFor(plantName: string, data: PlantFile = loadPlantFile()): PlantingResult {
  const wanted = plantName.trim().toLowerCase();
  const plant = data.plants.find((p) => p.name === wanted || `${p.name}s` === wanted || p.name === `${wanted}s`);
  if (!plant) return { found: false, knownPlants: data.plants.map((p) => p.name) };

  const plantOut = shiftWeeks(data.lastFrost, plant.transplantWeeks);
  return {
    found: true,
    plant: plant.name,
    sowIndoors: plant.sowIndoorsWeeks === null ? null : shiftWeeks(data.lastFrost, plant.sowIndoorsWeeks),
    plantOut,
    firstHarvest: new Date(new Date(`${plantOut}T00:00:00Z`).getTime() + plant.harvestDays * DAY_MS)
      .toISOString()
      .slice(0, 10),
    note: plant.note,
  };
}

export const plantingCalendar = tool({
  description:
    "Look up the sow-indoors, plant-out and first-harvest dates for a crop at the Hollyhock Lane garden.",
  inputSchema: z.object({
    plant: z.string().describe("Crop name, for example 'tomato' or 'peas'"),
  }),
  execute: async ({ plant }) => planFor(plant),
});
