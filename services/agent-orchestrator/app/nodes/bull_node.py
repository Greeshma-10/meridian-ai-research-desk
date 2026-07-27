"""Builds the strongest long (buy) thesis, grounded in retrieved chunks."""
import logging

from app.state import AgentState
from app.llm_client import ClaudeClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Bull Analyst at an investment research desk. Your job is to build \
the STRONGEST possible case for why an investor should be optimistic about this company, based \
ONLY on the provided research excerpts.

Rules:
- Every specific claim must cite which excerpt it came from, using [chunk_id].
- Do not invent facts not present in the excerpts.
- Be genuinely persuasive, not wishy-washy — argue your side with conviction.
- Keep it to 3-4 tight paragraphs."""


def bull_node(state: AgentState) -> AgentState:
    logger.info("[Bull] Building long thesis")
    client = ClaudeClient()

    excerpts = "\n\n".join(
        f"[{c['chunk_id']}] ({c['section_title']}): {c['text']}"
        for c in state["research_chunks"]
    )
    user_message = f"Company: {state['ticker']}\nQuestion: {state['query']}\n\nResearch excerpts:\n{excerpts}"

    state["bull_thesis"] = client.generate(SYSTEM_PROMPT, user_message, max_tokens=600)
    return state