"""
Retrieves relevant chunks for the query by calling the retrieval-service
over HTTP — this node has NO knowledge of Chroma, BM25, or reranking
internals. It only knows "send a query, get back ranked chunks."
"""
import logging

import requests

from app.state import AgentState

logger = logging.getLogger(__name__)

RETRIEVAL_SERVICE_URL = "http://localhost:8001"


def research_node(state: AgentState) -> AgentState:
    logger.info(f"[Research] Calling retrieval service for: {state['query']}")

    response = requests.post(
        f"{RETRIEVAL_SERVICE_URL}/search",
        json={"query": state["query"], "ticker": state["ticker"], "top_n": 8},
        timeout=30,
    )
    response.raise_for_status()
    results = response.json()["results"]

    state["research_chunks"] = [
        {
            "chunk_id": r["chunk_id"],
            "text": r["text"],
            "item_number": r["item_number"],
            "section_title": r["section_title"],
        }
        for r in results
    ]
    return state