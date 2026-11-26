import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe("with tracking disabled", () => {
  it("builds no span processors, so nothing can be exported", async () => {
    vi.stubEnv("OPIK_TRACK_DISABLE", "true");
    const { buildSpanProcessors, trackingDisabled } = await import("../src/observability.ts");
    expect(trackingDisabled).toBe(true);
    expect(buildSpanProcessors()).toEqual([]);
  });

  it("still runs a tool: the tracing layer never gets in the way", async () => {
    vi.stubEnv("OPIK_TRACK_DISABLE", "true");
    await import("../src/observability.ts");
    const { repairStatus, quoteRepair } = await import("../src/tools.ts");
    const ticket = await repairStatus.execute!({ ticket_id: "RT-2051" }, undefined as never);
    expect(ticket).toMatchObject({ status: "waiting_for_parts" });
    const quote = await quoteRepair.execute!({ part_skus: ["TB-700"], labor_jobs: ["tire-swap"] }, undefined as never);
    expect(quote).toMatchObject({ total_usd: 30.24 });
  });
});
