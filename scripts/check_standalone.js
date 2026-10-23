// Checks that the JavaScript scorer matches the Python scorer. Run after build_standalone.py:  node scripts/check_standalone.js
const fs = require("fs");
const path = require("path");
const { createScorer } = require("./scorer.js");

const dist = path.join(__dirname, "..", "dist");
const scorer = createScorer(JSON.parse(fs.readFileSync(path.join(dist, "data.json"), "utf8")));
const expected = JSON.parse(fs.readFileSync(path.join(dist, "parity.json"), "utf8"));

let worst = 0, verdictMiss = 0, typeMiss = 0, signalMiss = 0, scams = 0;
for (const e of expected) {
  const p = scorer.rawProbability(e.text);
  worst = Math.max(worst, Math.abs(p - e.scam_probability));
  const got = scorer.predict([e.text], false)[0];
  if (got.verdict !== e.verdict) verdictMiss++;
  if (e.verdict === "scam" && got.verdict === "scam") {
    scams++;
    if (got.scam_type_guess !== e.scam_type_guess) typeMiss++;
    if (JSON.stringify(got.signals) !== JSON.stringify(e.signals)) signalMiss++;
  }
}
console.log(`${expected.length} messages: max probability difference ${worst.toFixed(6)}, verdict differences ${verdictMiss}, scam type differences ${typeMiss}/${scams}, signal differences ${signalMiss}/${scams}`);
// Probabilities are rounded to 3 places in the reference, so allow that; one verdict may sit on a threshold.
const ok = worst < 0.0006 && verdictMiss <= 1 && typeMiss <= Math.ceil(scams * 0.01) && signalMiss <= Math.ceil(scams * 0.02);
console.log(ok ? "PARITY OK" : "PARITY FAILED");
process.exit(ok ? 0 : 1);
