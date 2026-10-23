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
