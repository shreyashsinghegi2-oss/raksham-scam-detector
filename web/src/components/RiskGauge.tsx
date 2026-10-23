import { type Band, bandOf } from "../lib/bands";

const G = { cx: 160, cy: 160, r: 128 };
const polar = (p: number, r = G.r): [number, number] => {
  const a = Math.PI + Math.PI * p;
  return [G.cx + r * Math.cos(a), G.cy + r * Math.sin(a)];
};
const arc = (from: number, to: number) => {
  const [x0, y0] = polar(from), [x1, y1] = polar(to);
  return `M${x0.toFixed(2)} ${y0.toFixed(2)} A${G.r} ${G.r} 0 0 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`;
};

type Props = { p: number | null; bands: Band[] };

export function RiskGauge({ p, bands }: Props) {
  const band = p === null ? null : bandOf(bands, p);
  const text = p === null ? "No message checked yet" : `${(p * 100).toFixed(1)} percent, ${band!.name} risk`;
  return (
    <figure className="mx-auto w-full max-w-[380px]" aria-label={"Risk meter: " + text}>
      <svg viewBox="0 0 320 188" className="block w-full overflow-visible" role="img" aria-hidden="true">
        {bands.map((b) => (
          <path key={b.name} d={arc(b.from + 0.003, b.to - 0.003)} fill="none" stroke={b.color} strokeWidth="5" strokeLinecap="butt" opacity={band && band.name !== b.name ? 0.28 : 1} style={{ transition: "opacity .5s" }} />
        ))}
        {Array.from({ length: 21 }, (_, i) => {
          const [x0, y0] = polar(i / 20, G.r + (i % 5 ? 11 : 9));
          const [x1, y1] = polar(i / 20, G.r + 15);
          return <line key={i} x1={x0} y1={y0} x2={x1} y2={y1} stroke="#52525b" strokeWidth="1" />;
        })}
        <text x={polar(0)[0]} y={polar(0)[1] + 28} textAnchor="middle" className="fill-zinc-600 text-[10px]">0</text>
        <text x={polar(1)[0]} y={polar(1)[1] + 28} textAnchor="middle" className="fill-zinc-600 text-[10px]">100</text>
        <g style={{ transformOrigin: `${G.cx}px ${G.cy}px`, transform: `rotate(${((p ?? 0) * 180).toFixed(1)}deg)`, transition: "transform .9s cubic-bezier(.2,.8,.2,1)" }}>
          <line x1={G.cx} y1={G.cy} x2={G.cx - G.r + 12} y2={G.cy} stroke="#fafafa" strokeWidth="2" strokeLinecap="round" />
        </g>
        <circle cx={G.cx} cy={G.cy} r="5" fill="#030303" stroke="#fafafa" strokeWidth="2" />
      </svg>
      <div className="-mt-1 text-center">
        <div className="tnum text-5xl font-semibold tracking-tight" style={{ color: band?.color ?? "#52525b" }}>
          {p === null ? "—" : (p * 100).toFixed(1)}
          {p !== null && <span className="ml-0.5 text-2xl text-zinc-500">%</span>}
        </div>
        <div className="label mt-2" style={{ color: band?.color }}>{band ? band.name + " risk" : "Awaiting message"}</div>
      </div>
      <ul className="mt-6 flex flex-wrap justify-center gap-x-5 gap-y-1.5 text-[11px] text-zinc-500">
        {bands.map((b) => (
          <li key={b.name} className="flex items-center gap-1.5">
            <i className="h-1.5 w-3 rounded-full" style={{ background: b.color }} />
            {b.name} <span className="tnum text-zinc-600">{Math.round(b.from * 100)}–{Math.round(b.to * 100)}</span>
          </li>
        ))}
      </ul>
    </figure>
  );
}
