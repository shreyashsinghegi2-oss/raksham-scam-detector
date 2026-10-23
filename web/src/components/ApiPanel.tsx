export function ApiPanel() {
  const site = location.protocol.startsWith("http") ? location.origin : "https://YOUR-SITE.vercel.app";
  const curl = `curl -X POST ${site}/api/predict \\\n  -H "content-type: application/json" \\\n  -d '{"messages": ["Your KYC has expired. Share the OTP now."]}'`;
  return (
    <section aria-label="Free API" className="grid gap-8 border-t border-white/[0.06] py-10 md:grid-cols-2">
      <div>
        <h2 className="label mb-3">Free API</h2>
        <p className="text-sm text-zinc-400">The same check as a JSON API. No key, no sign-up. It takes 1 to 50 messages of up to 2,000 characters.</p>
        <ul className="mt-4 space-y-1.5 text-sm text-zinc-500">
          <li><code className="text-zinc-300">POST /api/predict</code> returns a verdict, a score, the likely type and the words behind it.</li>
          <li><code className="text-zinc-300">GET /api/health</code> reports the model and a built-in self-check.</li>
          <li><a href="/api/docs" className="text-accent underline-offset-4 hover:underline">Interactive documentation</a></li>
        </ul>
      </div>
      <pre className="overflow-x-auto rounded-lg bg-surface p-4 font-mono text-[12.5px] leading-relaxed text-zinc-300 ring-1 ring-white/[0.06]">{curl}</pre>
    </section>
  );
}
