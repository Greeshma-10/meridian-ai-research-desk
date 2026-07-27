"""Builds the strongest counter-thesis, directly attacking the Bull's claims."""
import logging

from app.state import AgentState
from app.llm_client import ClaudeClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Bear/Skeptic Analyst at an investment research desk. Your job is to \
build the STRONGEST possible case for caution or pessimism about this company, based ONLY on the \
provided research excerpts.

Rules:
- Directly address and challenge specific claims made in the Bull thesis provided to you.
- Every specific claim must cite which excerpt it came from, using [chunk_id].
- Do not invent facts not present in the excerpts.
- Keep it to 3-4 tight paragraphs."""


def bear_node(state: AgentState) -> AgentState:
    logger.info("[Bear] Building counter-thesis")
    client = ClaudeClient()

    excerpts = "\n\n".join(
        f"[{c['chunk_id']}] ({c['section_title']}): {c['text']}"
        for c in state["research_chunks"]
    )
    user_message = (
        f"Company: {state['ticker']}\nQuestion: {state['query']}\n\n"
        f"Research excerpts:\n{excerpts}\n\n"
        f"Bull Analyst's thesis (your job is to challenge this):\n{state['bull_thesis']}"
    )

    state["bear_thesis"] = client.generate(SYSTEM_PROMPT, user_message, max_tokens=600)
    return state