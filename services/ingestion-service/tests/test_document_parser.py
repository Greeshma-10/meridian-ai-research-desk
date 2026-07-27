"""
Unit tests for document_parser.py — specifically regression-testing the
iXBRL hidden-metadata stripping fix from Milestone 4.
"""
from app.document_parser import DocumentParser


def test_strips_script_and_style_tags(messy_html_with_hidden_xbrl):
    parser = DocumentParser()
    clean_text = parser.html_to_clean_text(messy_html_with_hidden_xbrl)

    assert "console.log" not in clean_text
    assert "color: red" not in clean_text


def test_strips_hidden_ixbrl_metadata(messy_html_with_hidden_xbrl):
    """
    Regression test for the Milestone 4 bug: fasb.org taxonomy URLs
    leaking into clean text via iXBRL's hidden metadata block.
    """
    parser = DocumentParser()
    clean_text = parser.html_to_clean_text(messy_html_with_hidden_xbrl)

    assert "fasb.org" not in clean_text
    assert "Hidden metadata that should be stripped" not in clean_text


def test_preserves_real_visible_content(messy_html_with_hidden_xbrl):
    parser = DocumentParser()
    clean_text = parser.html_to_clean_text(messy_html_with_hidden_xbrl)

    assert "SECURITIES AND EXCHANGE COMMISSION" in clean_text
    assert "Apple Inc." in clean_text