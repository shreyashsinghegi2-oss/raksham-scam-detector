import argparse
import csv
from pathlib import Path

from .data import ROOT
from .model import binary_metrics
from .predict import load_bundle, predict

DEFAULT = ROOT / "tests" / "handwritten_messages.csv"


def main() -> None:
    """Score the model on hand-written messages that are not from the dataset, including hard genuine ones
    (OTP and bank alerts). This is a small smoke test of behaviour outside the dataset's style, not a benchmark."""
    parser = argparse.ArgumentParser(description="Evaluate on a CSV with columns text,label,note (label 1 = scam).")
    parser.add_argument("csv", nargs="?", type=Path, default=DEFAULT)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    with open(args.csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    bundle = load_bundle()
    results = predict([r["text"] for r in rows], bundle, strict=args.strict)
    wrong = 0
    for row, res in zip(rows, results):
        truth = "scam" if row["label"] == "1" else "genuine"
        ok = truth == res["verdict"]
        wrong += not ok
        print(f"{'ok ' if ok else 'MISS'} truth={truth:7} p={res['scam_probability']:.2f}  [{row['note']}] {row['text'][:80]}")
    m = binary_metrics([int(r["label"]) for r in rows], [r["scam_probability"] for r in results], bundle["thresholds"]["strict" if args.strict else "balanced"])
    print(f"\n{len(rows)} messages: accuracy {m['accuracy']}, recall {m['recall']}, false positive rate {m['false_positive_rate']}, misses {wrong}")


if __name__ == "__main__":
    main()
