"""Scores messages with the exported Raksham model using NumPy only (no scikit-learn, no pickle).

It reproduces scikit-learn's TfidfVectorizer for the two analyzers the model uses (word n-grams and character n-grams
inside word boundaries), then applies logistic regression. tests/test_lite_parity.py checks it against scikit-learn.
"""
import json
import math
import re
import unicodedata
from pathlib import Path

import numpy as np

_WORD = re.compile(r"(?u)\b\w\w+\b")  # scikit-learn's default token pattern
_RUNS = re.compile(r"\s\s+")
TYPE_MIN_CONFIDENCE = 0.5


def word_ngrams(text: str, lo: int, hi: int) -> list[str]:
    tokens = _WORD.findall(text.lower())
    grams = []
    for n in range(lo, hi + 1):
        grams.extend(" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1))
    return grams


def char_wb_ngrams(text: str, lo: int, hi: int) -> list[str]:
    grams = []
    for word in _RUNS.sub(" ", text.lower()).split():
        word = f" {word} "
        for n in range(lo, hi + 1):
            offset = 0
            grams.append(word[offset:offset + n])
            while offset + n < len(word):
                offset += 1
                grams.append(word[offset:offset + n])
            if offset == 0:  # a word shorter than n counts once
                break
    return grams


class Space:
    """Word and character TF-IDF features, each L2-normalised, laid side by side."""

    def __init__(self, spec: dict, vocabs: dict, weights, prefix: str):
        self.parts = []
        for name, analyzer in (("word", word_ngrams), ("char", char_wb_ngrams)):
            part = spec[name]
            self.parts.append((analyzer, part["ngram"], part["offset"], vocabs[f"{prefix}_{name}"], weights[f"{prefix}_{name}_idf"].astype(np.float64)))
        self.features = spec["features"]
        self.word_terms = [""] * spec["word"]["size"]
        for term, i in vocabs[f"{prefix}_word"].items():
            self.word_terms[i] = term

    def vector(self, text: str) -> tuple[np.ndarray, np.ndarray]:
        all_idx, all_val = [], []
        for analyzer, (lo, hi), offset, vocab, idf in self.parts:
            counts: dict[int, int] = {}
            for gram in analyzer(text, lo, hi):
                j = vocab.get(gram)
                if j is not None:
                    counts[j] = counts.get(j, 0) + 1
            if not counts:
                continue
            idx = np.fromiter(counts.keys(), dtype=np.int64, count=len(counts))
            val = (1.0 + np.log(np.fromiter(counts.values(), dtype=np.float64, count=len(counts)))) * idf[idx]
            norm = float(np.sqrt((val * val).sum()))
            all_idx.append(idx + offset)
            all_val.append(val / norm if norm else val)
        if not all_idx:
            return np.empty(0, dtype=np.int64), np.empty(0)
        return np.concatenate(all_idx), np.concatenate(all_val)


class Lite:
    def __init__(self, folder: Path):
        self.meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        vocabs = json.loads((folder / "vocab.json").read_text(encoding="utf-8"))
        with np.load(folder / "weights.npz") as w:
            weights = {k: w[k] for k in w.files}
        self.det = Space(self.meta["det_space"], vocabs, weights, "det")
        self.kind = Space(self.meta["type_space"], vocabs, weights, "type")
        self.det_coef = weights["det_coef"].astype(np.float64)
        self.det_b = self.meta["det_intercept"]
        self.type_coef = weights["type_coef"].astype(np.float64)
        self.type_b = weights["type_intercept"]
        self.classes = self.meta["type_classes"]
        self.stop = set(self.meta["stop_words"])

    def probability(self, idx, val) -> float:
        z = float(val @ self.det_coef[idx]) + self.det_b
        return 1.0 / (1.0 + math.exp(-z)) if z >= 0 else math.exp(z) / (1.0 + math.exp(z))

    def type_probabilities(self, text: str) -> np.ndarray:
        idx, val = self.kind.vector(text)
        z = self.type_coef[:, idx] @ val + self.type_b
        e = np.exp(z - z.max())
        return e / e.sum()

    def signals(self, idx, val, k: int = 3) -> list[str]:
        """The words that pushed the score toward 'scam' the most, leaving out filler words and bare numbers."""
        found = []
        for position in np.argsort(idx, kind="stable"):  # feature order, so exact ties resolve the way scikit-learn resolves them
            j, v = int(idx[position]), float(val[position])
            if j >= self.det.parts[1][2]:  # character features are not words
                continue
            contribution = v * float(self.det_coef[j])
            term = self.det.word_terms[j]
            if contribution > 0 and not all(w in self.stop or w.isdigit() for w in term.split()):
                found.append((contribution, term))
        return [term for _, term in sorted(found, key=lambda pair: -pair[0])[:k]]

    def predict(self, texts: list[str], strict: bool = False) -> list[dict]:
        threshold = self.meta["thresholds"]["strict" if strict else "balanced"]
        results = []
        for text in texts:
            text = unicodedata.normalize("NFKC", text)  # fancy-font letters (𝙮𝙤𝙪𝙧) become plain ones
            idx, val = self.det.vector(text)
            p = self.probability(idx, val)
            item = {"verdict": "scam" if p >= threshold else "genuine", "scam_probability": round(p, 3)}
            if p >= threshold:
                kinds = self.type_probabilities(text)
                top = int(kinds.argmax())
                confidence = round(float(kinds[top]), 3)
                item["scam_type"] = self.classes[top] if confidence >= TYPE_MIN_CONFIDENCE else "uncertain"
                item["scam_type_guess"] = self.classes[top]
                item["scam_type_confidence"] = confidence
                item["signals"] = self.signals(idx, val)
            results.append(item)
        return results
