"""
Integration tests for retrieval-service — tests the REAL /index and
/search endpoints against the REAL running Chroma instance.
"""
import requests


def test_health_check(retrieval_url):
    response = requests.get(f"{retrieval_url}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_index_and_search_roundtrip(retrieval_url):
    """
    End-to-end proof: index a small, known set of fake chunks for a
    throwaway test ticker, then confirm searching for a specific known
    phrase actually retrieves the right chunk back. This is a REAL
    Bedrock embedding call and a REAL Chroma write/read — small but
    genuine cost per test run.
    """
    test_ticker = "TESTCO"
    chunk_ids = ["TESTCO_2025-01-01_1A_000", "TESTCO_2025-01-01_1A_001"]
    documents = [
        "TestCo faces significant competitive pressure from rival firms in the widget market.",
        "TestCo's supply chain depends on a single overseas manufacturing partner.",
    ]

    index_response = requests.post(
        f"{retrieval_url}/index",
        json={"ticker": test_ticker, "chunk_ids": chunk_ids, "documents": documents},
    )
    assert index_response.status_code == 200
    assert index_response.json()["chunk_count"] == 2

    search_response = requests.post(
        f"{retrieval_url}/search",
        json={"query": "competition from rivals", "ticker": test_ticker, "top_n": 1},
    )
    assert search_response.status_code == 200

    results = search_response.json()["results"]
    assert len(results) == 1
    assert results[0]["chunk_id"] == "TESTCO_2025-01-01_1A_000", (
        "Expected the competition-related chunk to rank first for a "
        "competition-related query — hybrid search + reranking may have regressed."
    )


def test_search_unindexed_ticker_returns_404(retrieval_url):
    """Confirms the service fails cleanly (not a 500 crash) for a ticker that was never indexed."""
    response = requests.post(
        f"{retrieval_url}/search",
        json={"query": "anything", "ticker": "NONEXISTENT_TICKER_XYZ", "top_n": 3},
    )
    assert response.status_code == 404