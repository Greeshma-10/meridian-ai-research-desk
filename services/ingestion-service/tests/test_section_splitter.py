"""
Unit tests for section_splitter.py — specifically targeting the
TOC-avoidance heuristic, since that's the subtlest piece of logic
and the easiest to silently break.
"""
from app.section_splitter import split_into_sections


def test_finds_all_expected_sections(sample_10k_text):
    sections = split_into_sections(sample_10k_text)
    item_numbers = [s.item_number for s in sections]

    assert "1" in item_numbers
    assert "1A" in item_numbers
    assert "7" in item_numbers


def test_ignores_table_of_contents_mentions(sample_10k_text):
    """
    This is THE critical test: the fixture text mentions "Item 1A" twice —
    once in a fake Table of Contents, once as the real section header.
    We must end up with exactly ONE "1A" section (the real one), not two,
    and its content must be the REAL section text, not the TOC line.
    """
    sections = split_into_sections(sample_10k_text)

    item_1a_sections = [s for s in sections if s.item_number == "1A"]
    assert len(item_1a_sections) == 1, (
        "Expected exactly one '1A' section — if this fails, the TOC-avoidance "
        "heuristic (using the LAST match, not first) has regressed."
    )

    # The section's actual content should be the real risk factors text,
    # not just the bare TOC line
    assert "faces competition" in item_1a_sections[0].text


def test_section_titles_are_captured_correctly(sample_10k_text):
    sections = split_into_sections(sample_10k_text)
    section_1a = next(s for s in sections if s.item_number == "1A")
    assert "Risk Factors" in section_1a.title


def test_handles_document_with_no_item_headers():
    """Edge case: what happens if the input doesn't look like a 10-K at all?"""
    plain_text = "This is just some random text with no Item headers at all."
    sections = split_into_sections(plain_text)

    assert len(sections) == 1
    assert sections[0].item_number == "UNKNOWN"