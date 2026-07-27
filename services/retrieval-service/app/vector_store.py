"""
Wraps Chroma for storing and querying chunk embeddings.
"""
import logging
import os

import chromadb

from app.chunker import Chunk

logger = logging.getLogger(__name__)

COLLECTION_NAME = "sec_filings"

# Read once at module level, used as the actual default below —
# falls back to "localhost" for local dev, overridden to the Cloud Map
# DNS name ("chroma.meridian.local") when running in ECS.
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")


class VectorStore:
    def __init__(self, host: str = CHROMA_HOST, port: int = 8000) -> None:
        self.client = chromadb.HttpClient(host=host, port=port)
        self.collection = self.client.get_or_create_collection(COLLECTION_NAME)

    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        """Stores chunks and their embeddings, with metadata for filtering later."""
        self.collection.add(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "ticker": c.ticker,
                    "filing_date": c.filing_date,
                    "item_number": c.item_number,
                    "section_title": c.section_title,
                }
                for c in chunks
            ],
        )
        logger.info(f"Added {len(chunks)} chunks to vector store")

    def query(self, query_embedding: list[float], n_results: int = 5, where: dict | None = None) -> dict:
        """Finds the n most semantically similar chunks, optionally filtered by metadata (e.g. ticker)."""
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )