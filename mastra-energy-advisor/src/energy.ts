// Pure energy maths, kept separate from the tools so it is easy to unit test.
import type { Appliance, DailyReading, Tariff } from "./data/home.ts";

const round = (n: number, digits = 2) => Number(n.toFixed(digits));

export function summarizeReadings(readings: DailyReading[]) {
  const peak = readings.reduce((s, r) => s + r.peakKwh, 0);
  const offPeak = readings.reduce((s, r) => s + r.offPeakKwh, 0);
  const total = peak + offPeak;
  return {
    days: readings.length,
    total_kwh: round(total),
    peak_kwh: round(peak),
    off_peak_kwh: round(offPeak),
    peak_share_pct: total === 0 ? 0 : round((peak / total) * 100, 1),
    avg_daily_kwh: readings.length === 0 ? 0 : round(total / readings.length),
  };
}

export function costOnTariff(readings: DailyReading[], tariff: Tariff) {
  const { peak_kwh, off_peak_kwh, total_kwh, days } = summarizeReadings(readings);
  const energy =
    tariff.flatRate !== undefined
      ? total_kwh * tariff.flatRate
      : peak_kwh * (tariff.peakRate ?? 0) + off_peak_kwh * (tariff.offPeakRate ?? 0);
  const standing = tariff.standingChargePerDay * days;
  return { energy_usd: round(energy), standing_usd: round(standing), total_usd: round(energy + standing) };
}

export function applianceDailyKwh(appliance: Appliance) {
  return round((appliance.watts / 1000) * appliance.typicalHoursPerDay, 3);
}

export function applianceDailyCost(appliance: Appliance, ratePerKwh: number) {
  return round(applianceDailyKwh(appliance) * ratePerKwh);
}
