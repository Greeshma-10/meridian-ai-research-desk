"""Independent risk assessment — doesn't argue a side, flags concerns."""
import logging

from app.state import AgentState
from app.llm_client import ClaudeClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Risk Manager at an investment research desk. You do not argue for \
or against the investment — your ONLY job is to identify concrete risk factors an investor should \
be aware of, based on the research and both analysts' arguments provided.

Rules:
- Stay neutral — you are not on the Bull's side or the Bear's side.
- Focus on: volatility, concentration risk, and any red flags either analyst may have understated.
- Every specific claim must cite which excerpt it came from, using [chunk_id] where applicable.
- Keep it to 2-3 tight paragraphs."""


def risk_node(state: AgentState) -> AgentState:
    logger.info("[Risk] Assessing risk")
    client = ClaudeClient()

    excerpts = "\n\n".join(
        f"[{c['chunk_id']}] ({c['section_title']}): {c['text']}"
        for c in state["research_chunks"]
    )
    user_message = (
        f"Company: {state['ticker']}\n\nResearch excerpts:\n{excerpts}\n\n"
        f"Bull thesis:\n{state['bull_thesis']}\n\nBear thesis:\n{state['bear_thesis']}"
    )

    state["risk_assessment"] = client.generate(SYSTEM_PROMPT, user_message, max_tokens=500)
    return state