"""The NumPy-only scorer that runs on Vercel must give the scikit-learn model's answers."""
import csv
import sys

import numpy as np
import pytest

from raksham import data
from raksham.export import DEPLOY_MODEL
from raksham.predict import load_bundle, predict

sys.path.insert(0, str(data.ROOT / "deploy" / "api"))
pytestmark = pytest.mark.skipif(
    not ((DEPLOY_MODEL / "weights.npz").exists() and data.DATA_PATH.exists() and data.EXTERNAL_PATH.exists() and data.MODEL_PATH.exists()),
    reason="needs the dataset, data/external and a trained model (raksham-train, raksham-export)",
)


@pytest.fixture(scope="module")
def models():
    from _lite import Lite

    return load_bundle(), Lite(DEPLOY_MODEL)


def sample_texts():
    df = data.load()
    rows = df.sample(600, random_state=1)["text"].tolist()
    ext = data.load_external().sample(200, random_state=1)["text"].tolist()
    with open(data.ROOT / "tests" / "handwritten_messages.csv", newline="", encoding="utf-8") as f:
        hand = [r["text"] for r in csv.DictReader(f)]
    return rows + ext + hand + ["", "   ", "ok", "₹5,00,000 जीतने के लिए OTP भेजें", "a" * 2000]


def test_probabilities_and_verdicts_match_scikit_learn(models):
    bundle, lite = models
    texts = sample_texts()
    expected = bundle["detector"].predict_proba(texts)[:, 1]
    got = np.array([lite.probability(*lite.det.vector(t)) for t in texts])
    assert np.abs(expected - got).max() < 1e-4
    for strict in (False, True):
        theirs = [r["verdict"] for r in predict(texts, bundle, strict=strict)]
        ours = [r["verdict"] for r in lite.predict(texts, strict=strict)]
        mismatches = sum(a != b for a, b in zip(theirs, ours))
        assert mismatches <= 1  # a probability within 1e-4 of the threshold may fall either side


def test_scam_type_and_signals_match(models):
    bundle, lite = models
    scams = [t for t, r in zip(sample_texts(), predict(sample_texts(), bundle)) if r["verdict"] == "scam"][:150]
    theirs, ours = predict(scams, bundle), lite.predict(scams)
    assert np.mean([a["scam_type_guess"] == b["scam_type_guess"] for a, b in zip(theirs, ours)]) > 0.99
    assert np.mean([a["signals"] == b["signals"] for a, b in zip(theirs, ours)]) > 0.97
