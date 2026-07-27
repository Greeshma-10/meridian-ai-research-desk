"""
Unit tests for chunker.py — verifying token-size targeting and that
metadata gets correctly attached to every resulting chunk.
"""
from app.section_splitter import DocumentSection
from app.chunker import chunk_sections, CHUNK_SIZE_TOKENS


def test_chunks_stay_within_reasonable_token_bounds():
    # A long synthetic section, long enough to force multiple sub-chunks
    long_text = "This is a sentence about business risk. " * 200
    section = DocumentSection(item_number="1A", title="Risk Factors", text=long_text)

    chunks = chunk_sections([section], ticker="TEST", filing_date="2025-01-01")

    assert len(chunks) > 1, "Expected the long section to be split into multiple chunks"

    for chunk in chunks:
        # Allow some tolerance above the target since RecursiveCharacterTextSplitter
        # respects sentence boundaries over hitting an exact token count
        assert chunk.token_count <= CHUNK_SIZE_TOKENS * 1.2, (
            f"Chunk {chunk.chunk_id} has {chunk.token_count} tokens, "
            f"well above the {CHUNK_SIZE_TOKENS} target"
        )


def test_chunk_metadata_is_correctly_attached():
    section = DocumentSection(item_number="1A", title="Risk Factors", text="Short risk text.")
    chunks = chunk_sections([section], ticker="AAPL", filing_date="2025-10-31")

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.ticker == "AAPL"
    assert chunk.filing_date == "2025-10-31"
    assert chunk.item_number == "1A"
    assert chunk.section_title == "Risk Factors"
    assert chunk.chunk_id == "AAPL_2025-10-31_1A_000"


def test_multiple_sections_produce_correctly_prefixed_chunk_ids():
    sections = [
        DocumentSection(item_number="1", title="Business", text="Business text here."),
        DocumentSection(item_number="1A", title="Risk Factors", text="Risk text here."),
    ]
    chunks = chunk_sections(sections, ticker="MSFT", filing_date="2025-07-30")

    item_1_chunks = [c for c in chunks if c.item_number == "1"]
    item_1a_chunks = [c for c in chunks if c.item_number == "1A"]

    assert len(item_1_chunks) == 1
    assert len(item_1a_chunks) == 1
    assert item_1_chunks[0].chunk_id.startswith("MSFT_2025-07-30_1_")
    assert item_1a_chunks[0].chunk_id.startswith("MSFT_2025-07-30_1A_")