// Fictional household "Willow Lane 14": a week of smart-meter readings, two
// electricity tariffs, and a small appliance catalogue. All canned, so only
// the LLM call leaves the machine.

export interface DailyReading {
  date: string;
  peakKwh: number; // 16:00-20:00
  offPeakKwh: number; // every other hour
}

export interface Tariff {
  id: string;
  name: string;
  standingChargePerDay: number; // USD
  flatRate?: number; // USD per kWh
  peakRate?: number;
  offPeakRate?: number;
}

export interface Appliance {
  id: string;
  name: string;
  watts: number;
  typicalHoursPerDay: number;
  shiftable: boolean; // can the household move it out of the peak window?
}

export const READINGS: DailyReading[] = [
  { date: "2025-03-03", peakKwh: 6.1, offPeakKwh: 9.4 },
  { date: "2025-03-04", peakKwh: 5.8, offPeakKwh: 9.0 },
  { date: "2025-03-05", peakKwh: 7.4, offPeakKwh: 10.2 },
  { date: "2025-03-06", peakKwh: 6.6, offPeakKwh: 9.7 },
  { date: "2025-03-07", peakKwh: 6.9, offPeakKwh: 9.3 },
  { date: "2025-03-08", peakKwh: 4.2, offPeakKwh: 12.8 },
  { date: "2025-03-09", peakKwh: 4.0, offPeakKwh: 13.1 },
];

export const TARIFFS: Record<string, Tariff> = {
  "flat-saver": {
    id: "flat-saver",
    name: "Flat Saver",
    standingChargePerDay: 0.46,
    flatRate: 0.27,
  },
  "evening-shift": {
    id: "evening-shift",
    name: "Evening Shift (time of use)",
    standingChargePerDay: 0.52,
    peakRate: 0.41,
    offPeakRate: 0.17,
  },
};

export const CURRENT_TARIFF_ID = "flat-saver";

export const APPLIANCES: Record<string, Appliance> = {
  "heat-pump-dryer": { id: "heat-pump-dryer", name: "Heat-pump tumble dryer", watts: 800, typicalHoursPerDay: 1.5, shiftable: true },
  dishwasher: { id: "dishwasher", name: "Dishwasher", watts: 1300, typicalHoursPerDay: 1.2, shiftable: true },
  "ev-charger": { id: "ev-charger", name: "EV wall charger (7 kW)", watts: 7000, typicalHoursPerDay: 1.5, shiftable: true },
  "oven": { id: "oven", name: "Electric oven", watts: 2200, typicalHoursPerDay: 0.8, shiftable: false },
  "fridge-freezer": { id: "fridge-freezer", name: "Fridge-freezer", watts: 90, typicalHoursPerDay: 24, shiftable: false },
};
