"""
BM25-based keyword search, complementing vector search's semantic matching
with literal term-overlap matching.

Design note: BM25 needs the full document corpus in memory to build its
index (it computes term frequencies across the whole collection, not per
document) — so we rebuild it from whatever is in Chroma at startup, rather
than maintaining a separate persistent store. Fine at our scale (hundreds
of chunks); a production system with millions of documents would use a
dedicated search engine (Elasticsearch/OpenSearch) instead.
"""
import logging

from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


class BM25Index:
    def __init__(self) -> None:
        self.chunk_ids: list[str] = []
        self.documents: list[str] = []
        self.bm25: BM25Okapi | None = None

    def build(self, chunk_ids: list[str], documents: list[str]) -> None:
        """Builds the BM25 index from a corpus of documents."""
        self.chunk_ids = chunk_ids
        self.documents = documents

        # BM25 works on tokenized text, not raw strings — simple whitespace
        # split is sufficient here since financial text doesn't need
        # heavy NLP preprocessing for this purpose
        tokenized_corpus = [doc.lower().split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info(f"Built BM25 index over {len(documents)} documents")

    def search(self, query: str, n_results: int = 15) -> list[tuple[str, float]]:
        """Returns [(chunk_id, bm25_score), ...] for the top matching chunks."""
        if self.bm25 is None:
            raise RuntimeError("BM25Index.build() must be called before search()")

        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        # Pair chunk_ids with scores, sort descending, take top N
        ranked = sorted(zip(self.chunk_ids, scores), key=lambda x: x[1], reverse=True)
        return ranked[:n_results]