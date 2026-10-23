import { ADVICE } from "../lib/bands";
import { FACTS, analyseLinks, presentFacts } from "../lib/analyse";
import type { BandName, Prediction } from "../lib/types";

type Props = { text: string; result: Prediction; band: BandName; flagged: boolean };

export function Findings({ text, result, band, flagged }: Props) {
  const found = presentFacts(text);
  const links = analyseLinks(text);
  const [headline, detail] = ADVICE[band];
  const guess = result.scam_type_guess?.replaceAll("_", " ");
  return (
    <div className="divide-y divide-white/[0.06]">
      <div className="pb-5">
        <p className="text-lg font-medium text-white">
          {flagged ? "Looks like a scam" : band === "High" || band === "Very high" ? "Not flagged in strict mode, but the score is high" : band === "Medium" ? "Not flagged, but take care" : "Not flagged as a scam"}
        </p>
        <p className="mt-1 text-sm text-zinc-400"><span className="font-medium text-zinc-200">{headline}</span> {detail}</p>
      </div>

      {flagged && (
        <dl className="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-2 py-5 text-sm">
          <dt className="text-zinc-500">Likely type</dt>
          <dd className="text-zinc-200">{result.scam_type === "uncertain" ? `Uncertain (best guess: ${guess})` : guess}</dd>
          {!!result.signals?.length && (<><dt className="text-zinc-500">Words behind it</dt><dd className="break-words text-zinc-200">{result.signals.join(", ")}</dd></>)}
        </dl>
      )}

      <div className="py-5">
        <p className="label mb-3">Signals in the text</p>
        <ul className="grid grid-cols-1 gap-x-8 gap-y-1.5 text-sm sm:grid-cols-2">
          {FACTS.map(([name]) => {
            const on = found.has(name);
            return (
              <li key={name} className={"flex items-center gap-2.5 " + (on ? "text-zinc-200" : "text-zinc-600")}>
                <span className={"h-1.5 w-1.5 rounded-full " + (on ? "bg-accent" : "bg-zinc-800")} aria-hidden="true" />
                {name}<span className="sr-only">{on ? ": found" : ": not found"}</span>
              </li>
            );
          })}
        </ul>
        <p className="mt-3 text-xs text-zinc-600">Plain pattern checks. They describe the message and do not change the score.</p>
      </div>

      {links.length > 0 && (
        <div className="pt-5">
          <p className="label mb-3">Link checks</p>
          <ul className="space-y-3 text-sm">
            {links.map((l) => (
              <li key={l.raw}>
                <span className="break-all font-mono text-[13px] text-zinc-200">{l.raw}</span>
                {l.notes.length ? (
                  <ul className="mt-1 list-disc space-y-0.5 pl-5 text-zinc-400">{l.notes.map((n) => <li key={n}>{n}</li>)}</ul>
                ) : (
                  <p className="mt-0.5 text-zinc-500">Nothing unusual in the address itself.</p>
                )}
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-zinc-600">Address patterns only. Links are not opened or looked up, so this does not show whether a site is safe.</p>
        </div>
      )}
    </div>
  );
}
