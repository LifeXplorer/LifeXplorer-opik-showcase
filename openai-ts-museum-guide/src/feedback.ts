import type { Opik } from "opik";

export const RATING_SCORE = "visitor-rating";

export interface VisitorRating {
  value: number;
  reason: string;
}

/**
 * Attach a visitor's rating to one turn's trace. It shows up as a `visitor-rating` column in the
 * trace list, so low-rated turns can be sorted to the top and opened.
 */
export async function logVisitorRating(opik: Opik, traceId: string, rating: VisitorRating): Promise<void> {
  if (rating.value < 0 || rating.value > 1) throw new RangeError("rating must be between 0 and 1");
  // Flush first: the score is applied to a trace the server must already know about.
  await opik.flush();
  // Feedback scores are keyed by trace id; the call returns nothing and is sent on the next flush.
  opik.logTracesFeedbackScores([
    { id: traceId, name: RATING_SCORE, value: rating.value, reason: rating.reason },
  ]);
  await opik.flush();
}
