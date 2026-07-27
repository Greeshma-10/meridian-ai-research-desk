"""
Integration tests for ingestion-service. We deliberately test against
AAPL, which is already indexed from earlier milestones — this exercises
the idempotency path (no new EDGAR fetch, no new embedding cost) rather
than triggering a full, costly re-ingestion on every test run.
"""
import requests


def test_health_check(ingestion_url):
    response = requests.get(f"{ingestion_url}/health")
    assert response.status_code == 200


def test_ingest_already_indexed_ticker_is_idempotent(ingestion_url):
    """
    AAPL was ingested in earlier milestones. Calling /ingest/AAPL again
    should short-circuit via the is_indexed check, NOT re-fetch from
    EDGAR or re-embed — this is the idempotency behavior from Milestone 9.
    """
    response = requests.post(f"{ingestion_url}/ingest/AAPL", timeout=30)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "already_indexed", (
        "Expected AAPL to already be indexed from prior milestones. "
        "If this fails, the idempotency check itself may be broken."
    )


def test_ingest_invalid_ticker_returns_clean_error(ingestion_url):
    """A ticker that doesn't exist on EDGAR should fail with a clear error, not crash."""
    response = requests.post(f"{ingestion_url}/ingest/ZZZZINVALID", timeout=30)
    body = response.json()
    assert body["status"] == "error"
    assert "No 10-K found" in body["detail"]