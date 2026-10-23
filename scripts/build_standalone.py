"""Build the browser demo: one HTML file with the scorer and the exported model inside it.

Run after raksham-export:  python scripts/build_standalone.py
Writes dist/raksham_scam_check.html, dist/data.json (the model data) and dist/parity.json (Python answers that
scripts/check_standalone.js compares the JavaScript scorer against).
"""
import base64
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "deploy" / "model"
sys.path.insert(0, str(ROOT / "deploy" / "api"))

from _lite import Lite  # noqa: E402


def b64(array: np.ndarray, dtype) -> str:
    return base64.b64encode(np.ascontiguousarray(array, dtype=dtype).tobytes()).decode("ascii")


def main() -> None:
    meta = json.loads((MODEL / "meta.json").read_text(encoding="utf-8"))
    vocabs = json.loads((MODEL / "vocab.json").read_text(encoding="utf-8"))
    with np.load(MODEL / "weights.npz") as w:
        arrays = {k: b64(w[k], np.float32 if k == "type_coef" else np.float64) for k in w.files}
    data = {"meta": meta, "vocabs": vocabs, "arrays": arrays}

    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    (dist / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    template = (ROOT / "scripts" / "standalone_template.html").read_text(encoding="utf-8")
    scorer = (ROOT / "scripts" / "scorer.js").read_text(encoding="utf-8")
    page = template.replace("/*SCORER*/", scorer).replace("/*DATA*/", json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
    (dist / "raksham_scam_check.html").write_text(page, encoding="utf-8")  # page content for the claude.ai artifact
    local = '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">' + page
    (dist / "raksham_scam_check.local.html").write_text(local, encoding="utf-8")  # the same page as a standalone file

    # Reference answers from the Python scorer for the parity check.
    import pandas as pd
    sys.path.insert(0, str(ROOT / "src"))
    from raksham import data as rdata

    df = rdata.load()
    texts = df.sample(400, random_state=5)["text"].tolist() + rdata.load_external().sample(150, random_state=5)["text"].tolist()
    texts += [r["text"] for r in pd.read_csv(ROOT / "tests" / "handwritten_messages.csv").to_dict("records")]
    texts += ["", "ok", "₹5,00,000 जीतने के लिए OTP भेजें", "Hello\tworld\n\nthis  is   spaced", "Pay now 🚨🚨 or account blocked __proto__ constructor", "a" * 1500]
    lite = Lite(MODEL)
    expected = [dict(r, text=t) for t, r in zip(texts, lite.predict(texts))]
    (dist / "parity.json").write_text(json.dumps(expected, ensure_ascii=False), encoding="utf-8")
    print(f"wrote dist/raksham_scam_check.html ({len(page) / 1e6:.1f} MB), data.json, parity.json ({len(texts)} messages)")


if __name__ == "__main__":
    main()
