"""
Shared state object passed between every node in the agent graph.
LangGraph nodes read from and write to this same object — each node
adds its output, later nodes can see everything produced before them.
"""
from typing import TypedDict


class ResearchChunk(TypedDict):
    chunk_id: str
    text: str
    item_number: str
    section_title: str


class AgentState(TypedDict):
    ticker: str
    query: str

    research_chunks: list[ResearchChunk]
    bull_thesis: str
    bear_thesis: str
    risk_assessment: str
    final_verdict: str