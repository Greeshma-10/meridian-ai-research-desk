"""
Runs citation verification against every agent's output, attaching a
per-agent trust report to the final state. This does NOT call any LLM
or AWS service — pure local computation, zero additional cost.
"""
import logging

from app.state import AgentState
from app.citation_verifier import verify_citations

logger = logging.getLogger(__name__)


def verification_node(state: AgentState) -> AgentState:
    logger.info("[Verification] Checking citations across all agent outputs")

    reports = {}
    for agent_name, text_key in [
        ("bull", "bull_thesis"),
        ("bear", "bear_thesis"),
        ("risk", "risk_assessment"),
        ("portfolio_manager", "final_verdict"),
    ]:
        report = verify_citations(state[text_key], state["research_chunks"])
        reports[agent_name] = {
            "total_citations": report.total_citations,
            "fabricated_count": report.fabricated_count,
            "low_support_count": report.low_support_count,
            "trust_score": round(report.trust_score, 2),
        }
    logger.info(f"Fabricated IDs (bull): {[c.chunk_id for c in report.checks if not c.exists]}")
    state["citation_verification"] = reports
    return state