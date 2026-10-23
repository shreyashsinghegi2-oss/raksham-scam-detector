type Sample = { label: string; text: string };

type Props = {
  value: string;
  onChange: (v: string) => void;
  strict: boolean;
  onStrict: (v: boolean) => void;
  onCheck: () => void;
  busy: boolean;
  samples: Sample[];
  onSample: (s: Sample) => void;
};

export const MAX = 2000;

export function InputPanel({ value, onChange, strict, onStrict, onCheck, busy, samples, onSample }: Props) {
  return (
    <section aria-label="Message to check" className="space-y-5">
      <div className="rounded-lg bg-surface ring-1 ring-white/[0.06] transition focus-within:ring-accent/50">
        <label htmlFor="msg" className="sr-only">Message</label>
        <textarea
          id="msg"
          value={value}
          maxLength={MAX}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) onCheck(); }}
          placeholder="Paste an SMS or WhatsApp message here. Remove names and account numbers first."
          className="block h-52 w-full resize-none rounded-lg bg-transparent p-4 text-[15px] leading-relaxed text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus-visible:ring-0 focus-visible:ring-offset-0"
        />
        <div className="flex items-center justify-between gap-4 border-t border-white/[0.06] px-4 py-3">
          <label className="flex cursor-pointer select-none items-center gap-3 text-sm text-zinc-400">
            <button
              type="button"
              role="switch"
              aria-checked={strict}
              onClick={() => onStrict(!strict)}
              className={"relative h-5 w-9 rounded-full transition-colors " + (strict ? "bg-accent" : "bg-zinc-700")}
            >
              <span className={"absolute top-0.5 h-4 w-4 rounded-full bg-ink transition-all " + (strict ? "left-[18px]" : "left-0.5")} />
            </button>
            Strict mode
          </label>
          <span className="tnum text-xs text-zinc-500">{value.length.toLocaleString()} / {MAX.toLocaleString()}</span>
        </div>
      </div>

      <button
        type="button"
        onClick={onCheck}
        disabled={busy}
        className="w-full rounded-md bg-accent px-5 py-3 text-sm font-semibold text-ink transition hover:bg-teal-300 active:scale-[0.99] active:bg-teal-400 disabled:cursor-wait disabled:opacity-60 sm:w-auto"
      >
        {busy ? "Analysing" : "Analyse message"}
      </button>

      <div>
        <p className="label mb-3">Try a sample</p>
        <div className="flex flex-wrap gap-2">
          {samples.map((s) => (
            <button
              key={s.label}
              type="button"
              onClick={() => onSample(s)}
              className="rounded-full bg-white/[0.04] px-3.5 py-1.5 text-[13px] text-zinc-300 transition hover:bg-white/[0.09] hover:text-white"
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
