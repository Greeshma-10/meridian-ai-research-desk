"""
Sub-chunks each document section into ~500-token pieces with overlap,
ready for embedding.

Uses LangChain's RecursiveCharacterTextSplitter configured to measure
length in TOKENS (via tiktoken) rather than characters — see section_splitter
docstring philosophy: we want units that match what the embedding model
actually sees.

Recursive splitting tries to break on paragraph breaks first, then
sentences, then words — only falling back to a hard character cut as a
last resort. This preserves natural language boundaries far better than
a blind fixed-size split.
"""
import logging
from dataclasses import dataclass

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.section_splitter import DocumentSection

logger = logging.getLogger(__name__)

CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 75  # ~15% overlap — enough to preserve continuity
                            # without excessive duplication across chunks

_encoding = tiktoken.get_encoding("cl100k_base")  # same tokenizer family used by
                                                    # OpenAI/many embedding models;
                                                    # good general-purpose default


def _token_length(text: str) -> int:
    """Counts tokens using tiktoken — this is what the splitter uses to decide chunk boundaries."""
    return len(_encoding.encode(text))


@dataclass
class Chunk:
    chunk_id: str          # e.g. "AAPL_2025-10-31_1A_003"
    ticker: str
    filing_date: str
    item_number: str        # which 10-K section this came from
    section_title: str
    text: str
    token_count: int


def chunk_sections(
    sections: list[DocumentSection],
    ticker: str,
    filing_date: str,
) -> list[Chunk]:
    """Sub-chunks every section and attaches metadata to each resulting chunk."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE_TOKENS,
        chunk_overlap=CHUNK_OVERLAP_TOKENS,
        length_function=_token_length,
        separators=["\n\n", "\n", ". ", " ", ""],  # tried in order, most natural first
    )

    all_chunks: list[Chunk] = []

    for section in sections:
        sub_texts = splitter.split_text(section.text)

        for i, sub_text in enumerate(sub_texts):
            chunk = Chunk(
                chunk_id=f"{ticker}_{filing_date}_{section.item_number}_{i:03d}",
                ticker=ticker,
                filing_date=filing_date,
                item_number=section.item_number,
                section_title=section.title,
                text=sub_text,
                token_count=_token_length(sub_text),
            )
            all_chunks.append(chunk)

    logger.info(f"Created {len(all_chunks)} chunks across {len(sections)} sections")
    return all_chunks