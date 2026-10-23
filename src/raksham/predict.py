import argparse
import json
import sys

import joblib

from .data import MODEL_PATH
from .model import explain

TYPE_MIN_CONFIDENCE = 0.5


def load_bundle(path=MODEL_PATH) -> dict:
    return joblib.load(path)


def predict(texts: list[str], bundle: dict | None = None, strict: bool = False) -> list[dict]:
    """Verdict, scam probability and, for scams, the likely scam type with its confidence and the words that drove the score.
    The strict threshold raises the bar for calling a message a scam, which cuts false alarms and misses more scams."""
    bundle = bundle or load_bundle()
    threshold = bundle["thresholds"]["strict" if strict else "balanced"]
    probs = bundle["detector"].predict_proba(texts)[:, 1]
    results = []
    for text, p in zip(texts, probs):
        is_scam = p >= threshold
        item = {"text": text, "verdict": "scam" if is_scam else "genuine", "scam_probability": round(float(p), 3)}
        if is_scam:
            kinds = bundle["type_model"].predict_proba([text])[0]
            top = int(kinds.argmax())
            guess, confidence = str(bundle["type_model"].classes_[top]), round(float(kinds[top]), 3)
            # Types are learned from only a few templates each, so a low-confidence guess is reported as uncertain.
            item["scam_type"] = guess if confidence >= TYPE_MIN_CONFIDENCE else "uncertain"
            item["scam_type_guess"] = guess
            item["scam_type_confidence"] = confidence
            item["signals"] = explain(bundle["explainer"], text)
        results.append(item)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify messages as scam or genuine.")
    parser.add_argument("messages", nargs="*", help="Message text. With none given, one message per line is read from standard input.")
    parser.add_argument("--strict", action="store_true", help="Fewer false alarms, more missed scams.")
    args = parser.parse_args()
    texts = args.messages or [line.strip() for line in sys.stdin if line.strip()]
    if not texts:
        parser.error("give at least one message")
    print(json.dumps(predict(texts, strict=args.strict), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
