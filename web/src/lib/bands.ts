import type { BandName } from "./types";

export type Band = { name: BandName; from: number; to: number; color: string };

/** Bands follow the model's two flag lines: High starts at the balanced line, Very high at the strict line,
 *  Medium at half the balanced line. They are a reading aid, not calibrated probabilities. */
export function bandsFor(t: { balanced: number; strict: number }): Band[] {
  const low = t.balanced / 2;
  return [
    { name: "Low", from: 0, to: low, color: "#3fb950" },
    { name: "Medium", from: low, to: t.balanced, color: "#e3b341" },
    { name: "High", from: t.balanced, to: t.strict, color: "#f0883e" },
    { name: "Very high", from: t.strict, to: 1, color: "#ff5c5c" },
  ];
}

export const bandOf = (bands: Band[], p: number) => bands.find((b) => p < b.to) ?? bands[bands.length - 1];

export const ADVICE: Record<BandName, [string, string]> = {
  "Very high": ["Do not reply, click or call.", "Do not share an OTP, PIN or password, and do not install any app it asks for. Contact the organisation only through its official app or the number on your card. Report it at cybercrime.gov.in or call 1930."],
  High: ["Treat this as a scam until proven otherwise.", "Do not click links or call numbers in the message. Check with the organisation through its official app or website."],
  Medium: ["Not flagged, but take care.", "If it asks for money, codes or urgent action, verify through an official channel before doing anything."],
  Low: ["No strong scam pattern found.", "This is not proof that a message is safe. Never share an OTP, PIN or password."],
};
