"""The Vercel app (deploy/api/index.py) runs on NumPy only and must behave like the local API."""
import importlib.util
import sys

import pytest
from fastapi.testclient import TestClient

from raksham import data
from raksham.export import DEPLOY_MODEL

pytestmark = pytest.mark.skipif(not (DEPLOY_MODEL / "weights.npz").exists(), reason="run raksham-train then raksham-export")

SCAM = "Your KYC has expired. Click http://bank-kyc-update.xyz and share the OTP now or your account will be blocked today."
GENUINE = "Mom I reached the hostel safely, will call you after dinner."


@pytest.fixture(scope="module")
def client():
    api = data.ROOT / "deploy" / "api"
    sys.path.insert(0, str(api))
    spec = importlib.util.spec_from_file_location("deploy_index", api / "index.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return TestClient(module.app), module


def test_health_self_check_passes(client):
    body = client[0].get("/api/health").json()
    assert body["status"] == "ok" and body["self_check"] == [True, True]
    assert body["thresholds"]["strict"] > body["thresholds"]["balanced"]


def test_predict_and_input_limits(client):
    c, m = client
    results = c.post("/api/predict", json={"messages": [SCAM, GENUINE]}).json()["results"]
    assert [r["verdict"] for r in results] == ["scam", "genuine"] and [r["index"] for r in results] == [0, 1]
    assert c.post("/api/predict", json={"messages": []}).status_code == 422
    assert c.post("/api/predict", json={"messages": ["   "]}).status_code == 422
    assert c.post("/api/predict", json={"messages": ["x"] * (m.MAX_MESSAGES + 1)}).status_code == 422
    assert c.post("/api/predict", json={"messages": ["x" * (m.MAX_CHARS + 1)]}).status_code == 422


def test_api_key_when_set(client, monkeypatch):
    c, _ = client
    monkeypatch.setenv("RAKSHAM_API_KEY", "secret")
    body = {"messages": [GENUINE]}
    assert c.post("/api/predict", json=body).status_code == 401
    assert c.post("/api/predict", json=body, headers={"x-api-key": "secret"}).status_code == 200
    assert c.get("/api/health").status_code == 200  # health stays open


def test_the_function_needs_only_fastapi_and_numpy():
    sources = (data.ROOT / "deploy" / "api" / "index.py").read_text() + (data.ROOT / "deploy" / "api" / "_lite.py").read_text()
    assert "sklearn" not in sources and "pandas" not in sources and "joblib" not in sources


def test_page_is_self_contained_and_uses_the_api():
    public = data.ROOT / "deploy" / "public"
    page = (public / "index.html").read_text(encoding="utf-8")
    code = "".join(f.read_text(encoding="utf-8") for f in (public / "assets").glob("*.js"))  # the React build
    assert "/api/predict" in code and "/api/health" in code
    styles = "".join(f.read_text(encoding="utf-8") for f in (public / "assets").glob("*.css"))
    for text in (page, styles):
        assert 'src="http' not in text and 'href="http' not in text and "fonts.googleapis" not in text  # nothing is loaded from another site


def test_fancy_unicode_letters_are_read_as_plain_text():
    from fastapi.testclient import TestClient
    import index

    plain = "your credit card limit is being increased to rs 2 lakh please confirm the otp and cvv for activation"
    fancy = "𝙮𝙤𝙪𝙧 𝙘𝙧𝙚𝙙𝙞𝙩 𝙘𝙖𝙧𝙙 𝙡𝙞𝙢𝙞𝙩 𝙞𝙨 𝙗𝙚𝙞𝙣𝙜 𝙞𝙣𝙘𝙧𝙚𝙖𝙨𝙚𝙙 𝙩𝙤 𝙧𝙨 2 𝙡𝙖𝙠𝙝 𝙥𝙡𝙚𝙖𝙨𝙚 𝙘𝙤𝙣𝙛𝙞𝙧𝙢 𝙩𝙝𝙚 𝙤𝙩𝙥 𝙖𝙣𝙙 𝙘𝙫𝙫 𝙛𝙤𝙧 𝙖𝙘𝙩𝙞𝙫𝙖𝙩𝙞𝙤𝙣"
    r = TestClient(index.app).post("/api/predict", json={"messages": [plain, fancy]}).json()["results"]
    assert r[0]["scam_probability"] == r[1]["scam_probability"]
    assert r[1]["verdict"] == "scam"
