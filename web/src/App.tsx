import { useCallback, useEffect, useMemo, useState } from "react";
import { health as fetchHealth, predict } from "./lib/api";
import { bandOf, bandsFor } from "./lib/bands";
import type { Entry, Health, Prediction } from "./lib/types";
import { useHistory } from "./lib/useHistory";
import { ApiPanel } from "./components/ApiPanel";
import { Findings } from "./components/Findings";
import { Header } from "./components/Header";
import { History } from "./components/History";
import { InputPanel, MAX } from "./components/InputPanel";
import { RiskGauge } from "./components/RiskGauge";
import { Telemetry } from "./components/Telemetry";

const SAMPLES = [
  { label: "Bank KYC scam", text: "Dear customer your SBI YONO account will be blocked today. Update PAN now at http://sbi-kyc-update.xyz or call 98xxxxxx34" },
  { label: "Electricity scam", text: "Sir aapka bijli connection aaj raat 9:30 baje kat jayega, bill update nahi hua. Turant is number par call karein: 98xxxxxx12" },
  { label: "Fake job fee", text: "आपका चयन हो गया है। नौकरी पक्की करने के लिए Rs 1,500 पंजीकरण शुल्क अभी जमा करें।" },
  { label: "Bank debit alert (genuine)", text: "Rs 2,000.00 debited from A/c XX1234 on 12-10-26 at AMAZON. Not you? Call 1930 or the bank number on your card." },
  { label: "Insurance reminder", text: "Dear customer, your LIC premium of Rs 4,200 for policy 12345678 is due on 28 Oct. Pay at licindia.in or through your agent." },
  { label: "Salary credited (weak spot)", text: "Your salary of Rs 62,000 has been credited to account XX4521 on 30-Sep." },
];

const FALLBACK = { balanced: 0.71, strict: 0.93 };

export default function App() {
  const [text, setText] = useState("");
  const [strict, setStrict] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shown, setShown] = useState<{ text: string; result: Prediction } | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [status, setStatus] = useState<"checking" | "online" | "degraded" | "offline">("checking");
  const { entries, add, clear } = useHistory();

  useEffect(() => {
    fetchHealth().then((h) => { setHealth(h); setStatus(h.status === "ok" ? "online" : "degraded"); }).catch(() => setStatus("offline"));
  }, []);

  const bands = useMemo(() => bandsFor(health?.thresholds ?? FALLBACK), [health]);

  const check = useCallback(async (input?: string, useStrict = strict) => {
    const value = (input ?? text).trim();
    if (!value) { setError("Paste a message first."); return; }
    setBusy(true); setError(null);
    try {
      const result = await predict(value, useStrict);
      setShown({ text: value, result });
      add({ text: value.slice(0, MAX), p: result.scam_probability, band: bandOf(bands, result.scam_probability).name, flagged: result.verdict === "scam", type: result.verdict === "scam" ? (result.scam_type === "uncertain" ? "uncertain" : result.scam_type_guess ?? null) : null });
    } catch (e) {
      setError(e instanceof TypeError ? "Could not reach the service. Check your connection and try again." : (e as Error).message);
    } finally { setBusy(false); }
  }, [text, strict, add, bands]);

  const pick = (e: { text: string }) => { setText(e.text); void check(e.text); };
  const toggleStrict = (v: boolean) => { setStrict(v); if (text.trim()) void check(text, v); };

  const p = shown?.result.scam_probability ?? null;
  const band = p === null ? null : bandOf(bands, p);

  return (
    <div className="min-h-screen bg-ink">
      <Header status={status} />
      <main className="mx-auto max-w-[1280px] px-5 sm:px-8">
        <div className="grid grid-cols-[minmax(0,1fr)] gap-x-14 gap-y-12 py-12 lg:grid-cols-12 lg:py-16">
          <div className="min-w-0 lg:col-span-5">
            <p className="label mb-4 text-accent/80">Scam message check</p>
            <h1 className="text-balance text-4xl font-semibold leading-[1.08] tracking-tight text-white sm:text-5xl">How risky is this message?</h1>
            <p className="mt-4 max-w-md text-[15px] leading-relaxed text-zinc-400">
              Paste an SMS, WhatsApp message or call transcript in English, Hindi or Hinglish. You get a risk meter, the words behind it and a plain next step.
            </p>
            <div className="mt-8">
              <InputPanel value={text} onChange={setText} strict={strict} onStrict={toggleStrict} onCheck={() => void check()} busy={busy} samples={SAMPLES} onSample={(s) => { setText(s.text); void check(s.text); }} />
              {error && <p role="alert" className="mt-4 text-sm text-red-400">{error}</p>}
            </div>
          </div>

          <div className="min-w-0 space-y-12 lg:col-span-7">
            <section aria-label="Risk result" aria-live="polite" className="rounded-lg bg-surface px-6 py-8 ring-1 ring-white/[0.06] sm:px-10">
              <div className="mb-6 flex items-center justify-between">
                <h2 className="label">Risk meter</h2>
                {band && <span className="text-xs text-zinc-500">{strict ? "Strict mode" : "Balanced mode"}</span>}
              </div>
              <RiskGauge p={p} bands={bands} />
              <div className="mt-8 border-t border-white/[0.06] pt-6">
                {shown && band
                  ? <Findings text={shown.text} result={shown.result} band={band.name} flagged={shown.result.verdict === "scam"} />
                  : <p className="text-center text-sm text-zinc-600">Analyse a message or pick a sample. The needle moves to the risk level.</p>}
              </div>
            </section>

            <div className="grid grid-cols-[minmax(0,1fr)] gap-x-12 gap-y-10 md:grid-cols-2">
              <Telemetry health={health} entries={entries} />
              <History entries={entries} onPick={pick as (e: Entry) => void} onClear={clear} health={health} />
            </div>
          </div>
        </div>

        <ApiPanel />
        <section aria-label="About this model" className="border-t border-white/[0.06] py-10">
          <h2 className="label mb-3">What to know</h2>
          <ul className="max-w-3xl list-disc space-y-1.5 pl-5 text-sm text-zinc-500">
            <li>The model is trained on synthetic, template-written Indian scam and genuine messages. Its scores describe that data, not real-world accuracy.</li>
            <li>It can wrongly flag genuine notices such as salary credits and premium receipts. The scam type is a weak hint.</li>
            <li>The risk bands are a reading aid built on the model's two flag lines. They are not calibrated probabilities.</li>
            <li>A result is a warning to check, not proof. Scammers change their wording.</li>
          </ul>
        </section>
      </main>
      <footer className="border-t border-white/[0.06] py-8 text-xs leading-relaxed text-zinc-600">
        <div className="mx-auto max-w-[1280px] px-5 sm:px-8">
          Raksham Research Institute is a research demo by ArthaMind. Messages are scored in memory and are not stored on the server. Recent checks stay in this browser. Never share an OTP, PIN or password. Report fraud at cybercrime.gov.in or call 1930.
        </div>
      </footer>
    </div>
  );
}
