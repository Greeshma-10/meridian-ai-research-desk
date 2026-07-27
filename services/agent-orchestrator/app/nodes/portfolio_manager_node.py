"""Synthesizes everything into a final, balanced verdict."""
import logging

from app.state import AgentState
from app.llm_client import ClaudeClient

logger = logging.getLogger(__name__)

# This is the one node where reasoning quality matters most, so it's worth
# noting explicitly: swap ClaudeClient(model_id=SONNET_MODEL_ID) here first
# if you ever want to selectively upgrade quality on a budget.
SYSTEM_PROMPT = """You are the Portfolio Manager making the final call. You have read a Bull \
thesis, a Bear thesis, and a Risk assessment. Your job is to weigh them honestly — do not just \
pick the side that sounds more confident.

Structure your response EXACTLY as:
VERDICT: [Bullish / Bearish / Neutral]
CONFIDENCE: [Low / Medium / High]
REASONING: [2-3 paragraphs explaining how you weighed the disagreement between Bull and Bear, \
and what the Risk assessment changes about your view. Explicitly name where you think Bull or \
Bear overstated their case, if applicable.]"""


def portfolio_manager_node(state: AgentState) -> AgentState:
    logger.info("[Portfolio Manager] Synthesizing final verdict")
    client = ClaudeClient()

    user_message = (
        f"Company: {state['ticker']}\nQuestion: {state['query']}\n\n"
        f"Bull thesis:\n{state['bull_thesis']}\n\n"
        f"Bear thesis:\n{state['bear_thesis']}\n\n"
        f"Risk assessment:\n{state['risk_assessment']}"
    )

    state["final_verdict"] = client.generate(SYSTEM_PROMPT, user_message, max_tokens=700)
    return state