import pytest
from fastapi.testclient import TestClient

from raksham.api import MAX_MESSAGES, app
from raksham.data import MODEL_PATH

pytestmark = pytest.mark.skipif(not MODEL_PATH.exists(), reason="train first: raksham-train")

SCAM = "Your KYC has expired. Click http://bank-kyc-update.xyz and share the OTP now or your account will be blocked today."
GENUINE = "Mom I reached the hostel safely, will call you after dinner."
client = TestClient(app)


def test_health_reports_the_model():
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["thresholds"]["strict"] > body["thresholds"]["balanced"]


def test_predict_returns_results_in_order_without_echoing_text():
    response = client.post("/predict", json={"messages": [SCAM, GENUINE]})
    assert response.status_code == 200
    results = response.json()["results"]
    assert [r["index"] for r in results] == [0, 1]
    assert [r["verdict"] for r in results] == ["scam", "genuine"]
    assert all("text" not in r for r in results)


def test_input_limits():
    assert client.post("/predict", json={"messages": []}).status_code == 422
    assert client.post("/predict", json={"messages": ["   "]}).status_code == 422
    assert client.post("/predict", json={"messages": ["x"] * (MAX_MESSAGES + 1)}).status_code == 422
    assert client.post("/predict", json={"messages": ["x" * 2001]}).status_code == 422


def test_api_key_is_enforced_when_set(monkeypatch):
    monkeypatch.setenv("RAKSHAM_API_KEY", "secret")
    body = {"messages": [GENUINE]}
    assert client.post("/predict", json=body).status_code == 401
    assert client.post("/predict", json=body, headers={"x-api-key": "wrong"}).status_code == 401
    assert client.post("/predict", json=body, headers={"x-api-key": "secret"}).status_code == 200
