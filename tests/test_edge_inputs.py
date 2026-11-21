"""Unusual inputs must never crash the committed NumPy scorer or its API, and must return well-formed results.

These tests use only files that are committed to the repository (deploy/model), so they run in CI without the dataset.
"""
import importlib.util
import math
import sys

import pytest
from fastapi.testclient import TestClient

from raksham import data
from raksham.export import DEPLOY_MODEL

pytestmark = pytest.mark.skipif(not (DEPLOY_MODEL / "weights.npz").exists(), reason="deploy/model is missing")

SCAM = "Your KYC has expired. Click http://bank-kyc-update.xyz and share the OTP now or your account will be blocked today."

EDGE_INPUTS = {
    "empty": "",
    "whitespace": " \t\n  ",
    "single_character": "a",
    "digits_only": "0123456789" * 5,
    "punctuation_only": "!!! ??? ... ---",
    "very_long": "congratulations you won a prize " * 3000,
    "single_long_token": "a" * 100_000,
    "emoji_only": "😀🎉💰🔥👍🏽👨‍👩‍👧‍👦",
    "emoji_in_scam": "🎁 You won ₹5,00,000! Share your OTP now 🔥 http://prize-claim.xyz",
    "hindi": "आपका खाता बंद हो जाएगा। अभी OTP भेजें।",
    "hinglish": "Aapka KYC expire ho gaya hai, abhi link par click karke OTP share karein warna account block ho jayega",
    "mixed_script": "Your खाता will be blocked, साझा करें OTP अभी 立即 تأكيد now",
    "right_to_left": "تم حظر حسابك، أرسل رمز OTP الآن",
    "zero_width_and_controls": "your​ OTP‍ is\u0000 required\u0007 now﻿",
    "combining_marks": "é́́́ " * 50,
    "fullwidth_and_math_letters": "ｙｏｕｒ ａｃｃｏｕｎｔ ｉｓ ｂｌｏｃｋｅｄ 𝙨𝙝𝙖𝙧𝙚 𝙊𝙏𝙋",
    "astral_characters": "\U0001F600" * 500,
}


@pytest.fixture(scope="module")
def lite():
    sys.path.insert(0, str(data.ROOT / "deploy" / "api"))
    from _lite import Lite

    return Lite(DEPLOY_MODEL)


@pytest.fixture(scope="module")
def client():
    api = data.ROOT / "deploy" / "api"
    sys.path.insert(0, str(api))
    spec = importlib.util.spec_from_file_location("deploy_index_edge", api / "index.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return TestClient(module.app), module


def assert_well_formed(item: dict) -> None:
    assert item["verdict"] in {"scam", "genuine"}
    assert isinstance(item["scam_probability"], float)
    assert 0.0 <= item["scam_probability"] <= 1.0 and not math.isnan(item["scam_probability"])
    if item["verdict"] == "scam":
        assert {"scam_type", "scam_type_guess", "scam_type_confidence", "signals"} <= set(item)
        assert 0.0 <= item["scam_type_confidence"] <= 1.0
        assert isinstance(item["signals"], list)
    else:
        assert "scam_type" not in item


@pytest.mark.parametrize("name", EDGE_INPUTS)
@pytest.mark.parametrize("strict", [False, True])
def test_scorer_returns_a_well_formed_result(lite, name, strict):
    (item,) = lite.predict([EDGE_INPUTS[name]], strict=strict)
    assert_well_formed(item)


def test_empty_and_blank_text_is_not_called_a_scam(lite):
    for text in ("", " \t\n  "):
        (item,) = lite.predict([text])
        assert item["verdict"] == "genuine"


def test_scorer_is_deterministic_and_batch_order_does_not_matter(lite):
    texts = list(EDGE_INPUTS.values())
    first = lite.predict(texts)
    assert first == lite.predict(texts)
    assert lite.predict(texts[::-1])[::-1] == first  # a message's score never depends on its neighbours


def test_a_zero_width_character_inside_a_word_still_gives_a_valid_verdict(lite):
    assert lite.predict([SCAM])[0]["verdict"] == "scam"
    assert_well_formed(lite.predict([SCAM.replace("OTP", "OT\u200bP")])[0])


def test_api_accepts_every_edge_input_that_passes_validation(client):
    c, m = client
    for name, text in EDGE_INPUTS.items():
        if not text.strip() or len(text.strip()) > m.MAX_CHARS:
            continue  # rejected by validation, covered below
        response = c.post("/api/predict", json={"messages": [text]})
        assert response.status_code == 200, name
        assert_well_formed(response.json()["results"][0])


def test_api_length_limit_is_exact_and_counts_characters_not_bytes(client):
    c, m = client
    assert c.post("/api/predict", json={"messages": ["x" * m.MAX_CHARS]}).status_code == 200
    assert c.post("/api/predict", json={"messages": ["x" * (m.MAX_CHARS + 1)]}).status_code == 422
    assert c.post("/api/predict", json={"messages": ["😀" * m.MAX_CHARS]}).status_code == 200  # 2000 characters, 8000 bytes
    assert c.post("/api/predict", json={"messages": ["अ" * (m.MAX_CHARS + 1)]}).status_code == 422


def test_api_rejects_empty_and_blank_messages_and_wrong_types(client):
    c, _ = client
    for body in ({"messages": [""]}, {"messages": [" \n\t "]}, {"messages": [None]}, {"messages": [123]}, {"messages": "text"}, {}):
        assert c.post("/api/predict", json=body).status_code == 422, body
