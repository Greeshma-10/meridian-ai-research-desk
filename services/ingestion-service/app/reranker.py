"""
Cross-encoder reranking — scores (query, chunk) pairs jointly for higher
precision than embedding similarity alone, applied to a small candidate
set after hybrid retrieval has already narrowed things down.
"""
import logging

from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

# A well-established, small, fast cross-encoder trained specifically for
# search relevance ranking (MS MARCO is a standard search-ranking benchmark)
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class Reranker:
    def __init__(self) -> None:
        logger.info(f"Loading reranker model: {RERANKER_MODEL}")
        self.model = CrossEncoder(RERANKER_MODEL)

    def rerank(
        self,
        query: str,
        candidates: list[tuple[str, str]],  # [(chunk_id, chunk_text), ...]
        top_n: int = 5,
    ) -> list[tuple[str, str, float]]:
        """Returns [(chunk_id, chunk_text, relevance_score), ...] sorted best-first."""
        pairs = [(query, text) for _, text in candidates]
        scores = self.model.predict(pairs)

        scored = [
            (chunk_id, text, float(score))
            for (chunk_id, text), score in zip(candidates, scores)
        ]
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:top_n]