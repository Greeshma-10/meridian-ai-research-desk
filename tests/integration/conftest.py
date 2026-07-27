"""
Shared fixtures for integration tests. These tests hit REAL running
services over HTTP — Chroma, retrieval-service, ingestion-service,
agent-orchestrator, api-gateway must all be up before running this suite.

Design choice: we fail fast with a clear diagnostic message if a service
is unreachable, rather than letting pytest report a confusing raw
ConnectionError three layers deep in some test's internals.
"""
import pytest
import requests

SERVICES = {
    "chroma": "http://localhost:8000/api/v1/heartbeat",
    "retrieval-service": "http://localhost:8001/health",
    "ingestion-service": "http://localhost:8002/health",
    "agent-orchestrator": "http://localhost:8003/health",
    "api-gateway": "http://localhost:8080/health",
}


@pytest.fixture(scope="session", autouse=True)
def ensure_all_services_healthy():
    """
    Runs ONCE before the entire integration test session. Checks every
    service's health endpoint and fails immediately with a clear message
    naming exactly which service is down, rather than letting individual
    tests fail one by one with cryptic connection errors.
    """
    unreachable = []
    for name, url in SERVICES.items():
        try:
            response = requests.get(url, timeout=3)
            if response.status_code != 200:
                unreachable.append(f"{name} ({url}) returned status {response.status_code}")
        except requests.exceptions.RequestException:
            unreachable.append(f"{name} ({url}) is not reachable")

    if unreachable:
        pytest.exit(
            "\n\nIntegration tests require ALL services to be running first:\n"
            + "\n".join(f"  - {msg}" for msg in unreachable)
            + "\n\nStart the missing service(s) and re-run.",
            returncode=1,
        )


@pytest.fixture(scope="session")
def retrieval_url():
    return "http://localhost:8001"


@pytest.fixture(scope="session")
def ingestion_url():
    return "http://localhost:8002"


@pytest.fixture(scope="session")
def gateway_url():
    return "http://localhost:8080"