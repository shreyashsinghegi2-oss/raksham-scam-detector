import type { Entry, Health } from "../lib/types";

const pct = (v: number) => Math.round(v * 100) + "%";

function Metric({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="py-3.5">
      <dt className="text-xs text-zinc-500">{label}</dt>
      <dd className="tnum mt-1 text-2xl font-medium tracking-tight text-white">{value}</dd>
      {hint && <p className="mt-0.5 text-[11px] text-zinc-600">{hint}</p>}
    </div>
  );
}

export function Telemetry({ health, entries }: { health: Health | null; entries: Entry[] }) {
  const flagged = entries.filter((e) => e.flagged).length;
  const avg = entries.length ? entries.reduce((s, e) => s + e.p, 0) / entries.length : null;
  const ev = health?.evaluation;
  return (
    <section aria-label="Telemetry">
      <h2 className="label mb-1">Telemetry</h2>
      <dl className="grid grid-cols-2 divide-white/[0.06] sm:[&>*:nth-child(odd)]:pr-6 [&>*]:border-b [&>*]:border-white/[0.06]">
        <Metric label="Checks this browser" value={String(entries.length)} />
        <Metric label="Flagged" value={entries.length ? `${flagged}` : "—"} hint={entries.length ? `of ${entries.length}` : undefined} />
        <Metric label="Average score" value={avg === null ? "—" : (avg * 100).toFixed(1) + "%"} />
        <Metric label="Flag lines" value={health ? `${pct(health.thresholds.balanced)} / ${pct(health.thresholds.strict)}` : "—"} hint="balanced / strict" />
        <Metric label="Scam templates caught" value={ev ? pct(ev.scam_templates_caught) : "—"} hint="unseen templates" />
        <Metric label="Genuine left alone" value={ev ? pct(ev.genuine_templates_left_alone) : "—"} hint={ev ? `ROC AUC ${ev.roc_auc}` : undefined} />
      </dl>
    </section>
  );
}
