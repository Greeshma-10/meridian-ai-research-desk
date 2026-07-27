"""
Ingestion microservice — given a ticker, ensures it's fully indexed:
fetch from EDGAR -> parse -> chunk -> embed -> store in Chroma -> 
register BM25 index with retrieval-service.

Idempotent: checks with retrieval-service first, skips re-fetching
if the ticker's already indexed (saves EDGAR calls and Bedrock costs).
"""
import logging

import requests
from fastapi import FastAPI

from app.edgar_client import EdgarClient
from app.document_parser import DocumentParser
from app.section_splitter import split_into_sections
from app.chunker import chunk_sections
from app.embedder import BedrockEmbedder
from app.vector_store import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os

RETRIEVAL_SERVICE_URL = os.environ.get("RETRIEVAL_SERVICE_URL", "http://localhost:8001")

app = FastAPI(title="Meridian Ingestion Service")


@app.post("/ingest/{ticker}")
def ingest(ticker: str) -> dict:
    ticker = ticker.upper()

    # Idempotency check — don't re-fetch/re-embed if already done
    check = requests.get(f"{RETRIEVAL_SERVICE_URL}/is_indexed/{ticker}").json()
    if check["indexed"]:
        logger.info(f"{ticker} already indexed, skipping ingestion")
        return {"status": "already_indexed", "ticker": ticker}

    logger.info(f"Ingesting {ticker} for the first time...")
    edgar = EdgarClient()
    parser = DocumentParser()
    embedder = BedrockEmbedder()
    store = VectorStore()

    filing = edgar.get_latest_10k(ticker)
    if not filing:
        return {"status": "error", "detail": f"No 10-K found for ticker {ticker}"}

    raw_html = parser.download_raw_html(filing["document_url"])
    clean_text = parser.html_to_clean_text(raw_html)
    sections = split_into_sections(clean_text)
    chunks = chunk_sections(sections, ticker=ticker, filing_date=filing["filing_date"])

    logger.info(f"Embedding {len(chunks)} chunks for {ticker}...")
    embeddings = embedder.embed_batch([c.text for c in chunks])
    store.add_chunks(chunks, embeddings)

    # Register this ticker's BM25 index with the retrieval service
    requests.post(f"{RETRIEVAL_SERVICE_URL}/index", json={
        "ticker": ticker,
        "chunk_ids": [c.chunk_id for c in chunks],
        "documents": [c.text for c in chunks],
    })

    logger.info(f"Finished ingesting {ticker}: {len(chunks)} chunks")
    return {"status": "ingested", "ticker": ticker, "chunk_count": len(chunks)}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}