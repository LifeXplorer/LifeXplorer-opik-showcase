import type { Opik } from "opik";
import { describe, expect, it, vi } from "vitest";
import { logVisitorRating, RATING_SCORE } from "../src/feedback.js";

function fakeOpik() {
  return { flush: vi.fn(async () => {}), logTracesFeedbackScores: vi.fn() };
}

describe("logVisitorRating", () => {
  it("logs a named score on the trace between two flushes", async () => {
    const opik = fakeOpik();
    await logVisitorRating(opik as unknown as Opik, "trace-1", { value: 1, reason: "thumbs-up" });

    expect(opik.logTracesFeedbackScores).toHaveBeenCalledWith([
      { id: "trace-1", name: RATING_SCORE, value: 1, reason: "thumbs-up" },
    ]);
    expect(opik.flush).toHaveBeenCalledTimes(2);
  });

  it("rejects ratings outside 0..1", async () => {
    const opik = fakeOpik();
    await expect(logVisitorRating(opik as unknown as Opik, "t", { value: 4, reason: "x" })).rejects.toThrow(RangeError);
    expect(opik.logTracesFeedbackScores).not.toHaveBeenCalled();
  });
});
