"""Knowledge graph microservice — extraction + query endpoints."""
import logging

import requests
from fastapi import FastAPI
from pydantic import BaseModel

from app.graph_store import GraphStore
from app.entity_extractor import EntityExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RETRIEVAL_SERVICE_URL = "http://localhost:8001"

app = FastAPI(title="Meridian Knowledge Graph Service")
store = GraphStore()
extractor = EntityExtractor()


class BuildGraphRequest(BaseModel):
    ticker: str
    filing_date: str


@app.post("/build_graph")
def build_graph(req: BuildGraphRequest) -> dict:
    """Pulls this ticker's Risk Factors chunks and extracts entities/relationships into Neo4j."""
    store.add_company(req.ticker, req.filing_date)

    search = requests.post(f"{RETRIEVAL_SERVICE_URL}/search", json={
        "query": "risk factors competitors regulatory supply chain",
        "ticker": req.ticker, "top_n": 8,
    }).json()

    extracted_count = 0
    for chunk in search["results"]:
        data = extractor.extract(chunk["text"])
        for competitor in data.get("competitors", []):
            store.add_competitor_relationship(req.ticker, competitor, chunk["chunk_id"])
            extracted_count += 1
        for risk_category in data.get("risk_categories", []):
            store.add_risk_category(req.ticker, risk_category, chunk["chunk_id"])
            extracted_count += 1

    return {"ticker": req.ticker, "entities_extracted": extracted_count}


@app.get("/competitors/{ticker}")
def competitors(ticker: str) -> dict:
    return {"ticker": ticker, "competitors": store.get_competitors(ticker.upper())}


@app.get("/shared_risks/{ticker_a}/{ticker_b}")
def shared_risks(ticker_a: str, ticker_b: str) -> dict:
    return {"shared_risks": store.get_shared_risks(ticker_a.upper(), ticker_b.upper())}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}