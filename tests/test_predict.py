import pytest

from raksham.data import MODEL_PATH
from raksham.predict import load_bundle, predict

pytestmark = pytest.mark.skipif(not MODEL_PATH.exists(), reason="train first: raksham-train")

SCAM = "Your KYC has expired. Click http://bank-kyc-update.xyz and share the OTP now or your account will be blocked today."
GENUINE = "Mom I reached the hostel safely, will call you after dinner."


def test_obvious_scam_and_genuine():
    scam, genuine = predict([SCAM, GENUINE])
    assert scam["verdict"] == "scam" and genuine["verdict"] == "genuine"
    assert scam["scam_probability"] > genuine["scam_probability"]


def test_scam_output_fields_and_uncertain_type_is_labelled():
    scam = predict([SCAM])[0]
    assert {"scam_type", "scam_type_guess", "scam_type_confidence", "signals"} <= set(scam)
    assert scam["scam_type"] in (scam["scam_type_guess"], "uncertain")
    assert "scam_type" not in predict([GENUINE])[0]


def test_strict_threshold_is_higher():
    t = load_bundle()["thresholds"]
    assert t["strict"] > t["balanced"]
