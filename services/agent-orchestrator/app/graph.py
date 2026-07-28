"""Wires all nodes into a linear LangGraph pipeline."""
import logging

from langgraph.graph import StateGraph, END

from app.state import AgentState
from app.nodes.research_node import research_node
from app.nodes.bull_node import bull_node
from app.nodes.bear_node import bear_node
from app.nodes.risk_node import risk_node
from app.nodes.portfolio_manager_node import portfolio_manager_node
from app.nodes.verification_node import verification_node

logger = logging.getLogger(__name__)


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("research", research_node)
    graph.add_node("bull", bull_node)
    graph.add_node("bear", bear_node)
    graph.add_node("risk", risk_node)
    graph.add_node("portfolio_manager", portfolio_manager_node)
    graph.add_node("verification", verification_node)

    graph.set_entry_point("research")
    graph.add_edge("research", "bull")
    graph.add_edge("bull", "bear")
    graph.add_edge("bear", "risk")
    graph.add_edge("risk", "portfolio_manager")
    graph.add_edge("portfolio_manager", "verification")
    graph.add_edge("verification", END)

    return graph.compile()