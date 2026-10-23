"""HTTP service for the scam detector.

Messages are scored in memory and are not stored or logged by this app. Set RAKSHAM_API_KEY to require an
`x-api-key` header; leave it unset only for private networks or local use.
"""
import hmac
import os
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, StringConstraints

from .data import MODEL_PATH
from .predict import load_bundle, predict

MAX_MESSAGES = 50
MAX_CHARS = 2000

Message = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_CHARS)]


class PredictRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=MAX_MESSAGES)
    strict: bool = Field(default=False, description="Fewer false alarms, more missed scams.")


@lru_cache(maxsize=1)
def bundle() -> dict:
    if not MODEL_PATH.exists():
        raise HTTPException(503, "The model is not trained yet. Run raksham-train.")
    return load_bundle()


def require_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.environ.get("RAKSHAM_API_KEY")
    if expected and not hmac.compare_digest(x_api_key or "", expected):
        raise HTTPException(401, "Missing or wrong API key.")


app = FastAPI(title="Raksham Scam Detector", version="0.1.0")


@app.get("/health")
def health() -> dict:
    b = bundle()
    return {"status": "ok", "detector": b["detector_name"], "trained_on": b["trained_on"], "thresholds": b["thresholds"]}


@app.post("/predict", dependencies=[Depends(require_key)])
def predict_messages(request: PredictRequest) -> dict:
    results = predict(request.messages, bundle(), strict=request.strict)
    for index, item in enumerate(results):
        item.pop("text")  # the caller already has the text; results are in request order
        item["index"] = index
    return {"results": results}
