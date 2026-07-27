"""
Orchestrates the full retrieve-then-rerank pipeline:
  1. Run vector search AND BM25 search in parallel (same query)
  2. Merge results with Reciprocal Rank Fusion (RRF)
  3. Rerank the fused candidate set with a cross-encoder
  4. Return the final top results

RRF, not raw score averaging, is used to merge step 1's results on purpose:
vector similarity scores and BM25 scores live on completely different,
incomparable scales (cosine similarity is 0-1, BM25 scores are unbounded
and corpus-dependent) — averaging them directly would be mathematically
meaningless. RRF sidesteps this entirely by using each result's RANK
(1st place, 2nd place...) instead of its raw score, which is scale-free
by construction. This is the standard, well-established technique for
this exact problem.
"""
import logging

from app.vector_store import VectorStore
from app.keyword_search import BM25Index
from app.reranker import Reranker

logger = logging.getLogger(__name__)

RRF_K = 60  # standard constant from the original RRF paper — dampens the
             # impact of any single ranker's top result dominating the fusion


class HybridRetriever:
    def __init__(
        self,
        vector_store: VectorStore,
        bm25_index: BM25Index,
        reranker: Reranker,
    ) -> None:
        self.vector_store = vector_store
        self.bm25_index = bm25_index
        self.reranker = reranker

    def retrieve(
        self,
        query: str,
        query_embedding: list[float],
        candidate_pool_size: int = 15,
        final_top_n: int = 5,
    ) -> list[dict]:
        # Step 1a: vector search
        vector_results = self.vector_store.query(query_embedding, n_results=candidate_pool_size)
        vector_ids = vector_results["ids"][0]
        vector_docs = {cid: doc for cid, doc in zip(vector_ids, vector_results["documents"][0])}
        vector_meta = {cid: meta for cid, meta in zip(vector_ids, vector_results["metadatas"][0])}

        # Step 1b: keyword search
        bm25_results = self.bm25_index.search(query, n_results=candidate_pool_size)
        bm25_ids = [cid for cid, _ in bm25_results]

        # Step 2: Reciprocal Rank Fusion
        # score(doc) = sum over each ranker of 1 / (k + rank_in_that_ranker)
        rrf_scores: dict[str, float] = {}
        for rank, chunk_id in enumerate(vector_ids):
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (RRF_K + rank + 1)
        for rank, chunk_id in enumerate(bm25_ids):
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (RRF_K + rank + 1)

        fused_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
        fused_ids = fused_ids[:candidate_pool_size]

        # We need chunk text for every fused candidate. Vector search results
        # already carry text; BM25-only hits need their text pulled from the
        # BM25 index's own stored document list.
        bm25_doc_lookup = dict(zip(self.bm25_index.chunk_ids, self.bm25_index.documents))

        candidates = []
        for chunk_id in fused_ids:
            text = vector_docs.get(chunk_id) or bm25_doc_lookup.get(chunk_id)
            if text:
                candidates.append((chunk_id, text))

        logger.info(f"Fused {len(vector_ids)} vector + {len(bm25_ids)} BM25 results into {len(candidates)} candidates")

        # Step 3: rerank
        reranked = self.reranker.rerank(query, candidates, top_n=final_top_n)

        # Attach metadata back for display (fall back gracefully for BM25-only hits)
        results = []
        for chunk_id, text, score in reranked:
            meta = vector_meta.get(chunk_id, {"item_number": "?", "section_title": "?"})
            results.append({
                "chunk_id": chunk_id,
                "text": text,
                "score": score,
                "item_number": meta.get("item_number", "?"),
                "section_title": meta.get("section_title", "?"),
            })
        return results