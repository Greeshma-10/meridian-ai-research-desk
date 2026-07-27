"""
Retrieval microservice — exposes hybrid search + reranking over HTTP,
scoped per-ticker so multiple companies can be indexed simultaneously.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.vector_store import VectorStore
from app.keyword_search import BM25Index
from app.reranker import Reranker
from app.hybrid_retriever import HybridRetriever
from app.embedder import BedrockEmbedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

service_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing retrieval service resources...")
    service_state["store"] = VectorStore()
    service_state["embedder"] = BedrockEmbedder()
    service_state["reranker"] = Reranker()
    service_state["bm25_by_ticker"] = {}

    # Rebuild BM25 indexes from whatever tickers already exist in Chroma —
    # this is what makes the service survive a restart without losing state,
    # since Chroma's data is persisted to disk but our in-memory BM25 dict is not.
    _rebuild_bm25_from_chroma(service_state["store"], service_state["bm25_by_ticker"])

    logger.info(f"Retrieval service ready. Restored tickers: {list(service_state['bm25_by_ticker'].keys())}")
    yield
    service_state.clear()


def _rebuild_bm25_from_chroma(store: VectorStore, bm25_by_ticker: dict) -> None:
    """Pulls all stored chunks back out of Chroma, grouped by ticker, and rebuilds each ticker's BM25 index."""
    all_data = store.collection.get(include=["documents", "metadatas"])

    chunks_by_ticker: dict[str, dict[str, list]] = {}
    for chunk_id, doc, meta in zip(all_data["ids"], all_data["documents"], all_data["metadatas"]):
        ticker = meta["ticker"]
        chunks_by_ticker.setdefault(ticker, {"ids": [], "docs": []})
        chunks_by_ticker[ticker]["ids"].append(chunk_id)
        chunks_by_ticker[ticker]["docs"].append(doc)

    for ticker, data in chunks_by_ticker.items():
        bm25 = BM25Index()
        bm25.build(data["ids"], data["docs"])
        bm25_by_ticker[ticker] = bm25
        logger.info(f"Restored BM25 index for {ticker} ({len(data['ids'])} chunks)")


app = FastAPI(title="Meridian Retrieval Service", lifespan=lifespan)


class SearchRequest(BaseModel):
    query: str
    ticker: str
    top_n: int = 5


class SearchResultItem(BaseModel):
    chunk_id: str
    text: str
    score: float
    item_number: str
    section_title: str


class SearchResponse(BaseModel):
    results: list[SearchResultItem]


class IndexRequest(BaseModel):
    ticker: str
    chunk_ids: list[str]
    documents: list[str]


@app.post("/index")
def build_index(req: IndexRequest) -> dict:
    """Builds/refreshes the BM25 index for a SPECIFIC ticker — stored alongside any other tickers already indexed."""
    bm25 = BM25Index()
    bm25.build(req.chunk_ids, req.documents)
    service_state["bm25_by_ticker"][req.ticker] = bm25
    return {"status": "indexed", "ticker": req.ticker, "chunk_count": len(req.chunk_ids)}


@app.get("/is_indexed/{ticker}")
def is_indexed(ticker: str) -> dict:
    # Check the in-memory index first (fast path)
    if ticker in service_state["bm25_by_ticker"]:
        return {"ticker": ticker, "indexed": True}

    # Fall back to checking Chroma directly — handles the case where BM25
    # hasn't been rebuilt yet but the data genuinely exists
    existing = service_state["store"].collection.get(where={"ticker": ticker}, limit=1)
    return {"ticker": ticker, "indexed": len(existing["ids"]) > 0}

@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    bm25 = service_state["bm25_by_ticker"].get(req.ticker)
    if bm25 is None:
        raise HTTPException(status_code=404, detail=f"Ticker '{req.ticker}' has not been indexed yet")

    retriever = HybridRetriever(service_state["store"], bm25, service_state["reranker"])
    embedder = service_state["embedder"]

    query_embedding = embedder.embed_text(req.query)
    results = retriever.retrieve(req.query, query_embedding, ticker=req.ticker, final_top_n=req.top_n)

    return SearchResponse(results=[SearchResultItem(**r) for r in results])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}