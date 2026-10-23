type Props = { status: "checking" | "online" | "degraded" | "offline" };

const LABEL = { checking: "Checking service", online: "Service online", degraded: "Service degraded", offline: "Service unreachable" } as const;
const DOT = { checking: "bg-zinc-600", online: "bg-accent", degraded: "bg-amber-400", offline: "bg-red-400" } as const;

export function Header({ status }: Props) {
  return (
    <header className="sticky top-0 z-10 border-b border-white/[0.06] bg-ink/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-[1280px] items-center justify-between px-5 sm:px-8">
        <div className="flex items-center gap-3 text-sm">
          <svg viewBox="0 0 32 32" className="h-5 w-5 text-accent" aria-hidden="true">
            <path d="M16 4l10 3.8v7.7c0 6.4-4.3 10.7-10 12.8-5.7-2.1-10-6.4-10-12.8V7.8z" fill="none" stroke="currentColor" strokeWidth="2" />
          </svg>
          <span className="font-semibold tracking-[0.2em] text-white">RAKSHAM</span>
          <span className="h-4 w-px bg-white/10" aria-hidden="true" />
          <span className="hidden text-zinc-500 sm:inline">Research Institute</span>
        </div>
        <div role="status" className="flex items-center gap-2 text-xs text-zinc-400">
          <span className={"h-1.5 w-1.5 rounded-full " + DOT[status]} aria-hidden="true" />
          {LABEL[status]}
        </div>
      </div>
    </header>
  );
}
