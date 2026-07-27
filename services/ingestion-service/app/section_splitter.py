"""
Splits a 10-K's full text into its major legal sections (Item 1, Item 1A,
Item 7, etc.) before any sub-chunking happens.

Why this exists: 10-Ks have a legally mandated structure. Splitting along
these boundaries first means every chunk downstream carries a "section"
label — which lets retrieval later filter by section (e.g. "only search
Risk Factors") instead of treating the whole document as an undifferentiated
blob of text.

Known limitation (being upfront about it): 10-Ks include a Table of
Contents near the start that also lists "Item 1A" etc. as plain text.
A naive regex search would treat the TOC entries as section starts too.
We work around this with a simple heuristic: for each item number, take
its LAST occurrence in the document, not the first — the real section
header appears after the TOC, so the last match is far more likely to be
the actual content, not a listing.
"""
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Matches lines like "Item 1A." or "Item 7." at the start of a line,
# optionally followed by a section title on the same line
ITEM_PATTERN = re.compile(
    r"^Item\s+(\d+[A-Z]?)\.?\s*(.*)$",
    re.MULTILINE | re.IGNORECASE,
)


@dataclass
class DocumentSection:
    item_number: str      # e.g. "1A"
    title: str             # e.g. "Risk Factors"
    text: str               # the section's full text


def split_into_sections(full_text: str) -> list[DocumentSection]:
    """Splits a filing's clean text into its Item-based sections."""
    matches = list(ITEM_PATTERN.finditer(full_text))

    if not matches:
        logger.warning("No 'Item N' section headers found — returning whole document as one section")
        return [DocumentSection(item_number="UNKNOWN", title="Full Document", text=full_text)]

    # Keep only the LAST match per item number (see docstring: avoids
    # treating Table of Contents entries as real section starts)
    last_match_per_item: dict[str, re.Match] = {}
    for match in matches:
        item_number = match.group(1).upper()
        last_match_per_item[item_number] = match  # overwritten each time, so last wins

    # Sort the surviving matches by their position in the document
    ordered_matches = sorted(last_match_per_item.values(), key=lambda m: m.start())

    sections: list[DocumentSection] = []
    for i, match in enumerate(ordered_matches):
        start = match.start()
        end = ordered_matches[i + 1].start() if i + 1 < len(ordered_matches) else len(full_text)

        item_number = match.group(1).upper()
        title = match.group(2).strip() or "Untitled"
        section_text = full_text[start:end].strip()

        sections.append(DocumentSection(item_number=item_number, title=title, text=section_text))

    logger.info(f"Split document into {len(sections)} sections: {[s.item_number for s in sections]}")
    return sections