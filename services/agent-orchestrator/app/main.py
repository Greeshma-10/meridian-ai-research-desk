"""
Agent orchestration microservice — given a ticker and a question, runs
the full Research -> Bull -> Bear -> Risk -> Portfolio Manager pipeline
and returns the complete result.
"""
import logging

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.graph import build_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os
INGESTION_SERVICE_URL = os.environ.get("INGESTION_SERVICE_URL", "http://localhost:8002")

app = FastAPI(title="Meridian Agent Orchestrator")


class ResearchRequest(BaseModel):
    ticker: str
    query: str


class ResearchResponse(BaseModel):
    ticker: str
    query: str
    bull_thesis: str
    bear_thesis: str
    risk_assessment: str
    final_verdict: str


@app.post("/research", response_model=ResearchResponse)
def research(req: ResearchRequest) -> ResearchResponse:
    ticker = req.ticker.upper()
    logger.info(f"Starting research: {ticker} - {req.query}")

    ingest_result = requests.post(f"{INGESTION_SERVICE_URL}/ingest/{ticker}", timeout=120).json()
    if ingest_result.get("status") == "error":
        raise HTTPException(status_code=404, detail=ingest_result["detail"])

    graph = build_graph()
    result = graph.invoke({
        "ticker": ticker, "query": req.query,
        "research_chunks": [], "bull_thesis": "", "bear_thesis": "",
        "risk_assessment": "", "final_verdict": "",
    })

    return ResearchResponse(
        ticker=ticker,
        query=req.query,
        bull_thesis=result["bull_thesis"],
        bear_thesis=result["bear_thesis"],
        risk_assessment=result["risk_assessment"],
        final_verdict=result["final_verdict"],
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}