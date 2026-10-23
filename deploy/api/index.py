"""Raksham scam detector API for Vercel (FastAPI, NumPy only).

Messages are scored in memory and are not stored or logged by this app. Set RAKSHAM_API_KEY in the project's
environment variables to require an `x-api-key` header on /api/predict; leave it unset for a public demo.
"""
import hmac
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Annotated

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import Depends, FastAPI, Header
from pydantic import BaseModel, Field, StringConstraints

from _lite import Lite

MODEL_DIR = Path(__file__).resolve().parent.parent / "model"
MAX_MESSAGES = 50
MAX_CHARS = 2000

# Fixed examples used by /api/health to prove the deployed model scores correctly, without touching user data.
SELF_CHECK = [
    ("Your KYC has expired. Click http://bank-kyc-update.xyz and share the OTP now or your account will be blocked today.", "scam"),
    ("Mom I reached the hostel safely, will call you after dinner.", "genuine"),
]

Message = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_CHARS)]


class PredictRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=MAX_MESSAGES)
    strict: bool = Field(default=False, description="Fewer false alarms, more missed scams.")


@lru_cache(maxsize=1)
def model() -> Lite:
    return Lite(MODEL_DIR)


def require_key(x_api_key: str | None = Header(default=None)) -> None:
    from fastapi import HTTPException

    expected = os.environ.get("RAKSHAM_API_KEY")
    if expected and not hmac.compare_digest(x_api_key or "", expected):
        raise HTTPException(401, "Missing or wrong API key.")


app = FastAPI(title="Raksham Scam Detector", version="0.1.0", docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json")


@app.get("/api/health")
def health() -> dict:
    lite = model()
    results = lite.predict([text for text, _ in SELF_CHECK])
    checks = [r["verdict"] == expected for r, (_, expected) in zip(results, SELF_CHECK)]
    return {
        "status": "ok" if all(checks) else "degraded",
        "self_check": checks,
        "detector": lite.meta["detector"],
        "trained_on": lite.meta["trained_on"],
        "thresholds": lite.meta["thresholds"],
        "evaluation": lite.meta["evaluation"],
    }


@app.post("/api/predict", dependencies=[Depends(require_key)])
def predict_messages(request: PredictRequest) -> dict:
    results = model().predict(request.messages, strict=request.strict)
    for index, item in enumerate(results):
        item["index"] = index
    return {"results": results}
