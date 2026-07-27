"""
Full end-to-end test through the public api-gateway — the real path a
user's browser takes. Marked 'slow' since it triggers the entire
multi-agent pipeline (4 sequential Bedrock calls, ~20-40 seconds, real
cost each run) — excluded from the default test run, opt-in only.
"""
import pytest
import requests


@pytest.mark.slow
def test_full_analysis_pipeline_end_to_end(gateway_url):
    response = requests.post(
        f"{gateway_url}/analyze",
        json={"ticker": "AAPL", "query": "What is Apple's biggest competitive risk?"},
        timeout=120,
    )
    assert response.status_code == 200

    body = response.json()
    for field in ["bull_thesis", "bear_thesis", "risk_assessment", "final_verdict"]:
        assert field in body
        assert len(body[field]) > 50, f"{field} looks suspiciously short — possible truncated/failed generation"

    # Sanity check the PM verdict follows our required structure from the prompt design
    assert "VERDICT:" in body["final_verdict"]
    assert "CONFIDENCE:" in body["final_verdict"]