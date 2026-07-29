"""
Public-facing API gateway — the ONLY service the frontend talks to directly.

Honest scope note: a production gateway would also handle authentication,
rate limiting, and request validation beyond basic schema checking. We're
deliberately deferring those to a later hardening milestone so we can reach
a demoable state now — this is a conscious simplification, not an oversight.
"""
import logging

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import Depends
from app.auth import authenticate_user, create_access_token, verify_token
from pydantic import BaseModel as PydanticBaseModel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import os
from prometheus_fastapi_instrumentator import Instrumentator

AGENT_ORCHESTRATOR_URL = os.environ.get("AGENT_ORCHESTRATOR_URL", "http://localhost:8003")

app = FastAPI(title="Meridian API Gateway")
Instrumentator().instrument(app).expose(app)

# CORS: allows the frontend (served from a different port) to call this API
# from the browser. Wide open ("*") is fine for local dev; a real deployment
# would restrict this to the actual frontend's domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/login")
def login(req: LoginRequest) -> dict:
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(user["username"], user["role"])
    return {"access_token": token, "token_type": "bearer", "role": user["role"]}

class AnalyzeRequest(BaseModel):
    ticker: str
    query: str


@app.post("/analyze")
def analyze(req: AnalyzeRequest, user: dict = Depends(verify_token)) -> dict:
    logger.info(f"Gateway received request from {user['username']}: {req.ticker} - {req.query}")
    try:
        response = requests.post(
            f"{AGENT_ORCHESTRATOR_URL}/research",
            json={"ticker": req.ticker, "query": req.query},
            timeout=180,  # agent pipeline involves several sequential LLM calls — genuinely slow
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to reach agent-orchestrator: {e}")
        raise HTTPException(status_code=503, detail="Agent orchestrator service unavailable")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}