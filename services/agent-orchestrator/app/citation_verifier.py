"""
Verifies citations made by agents against the actual chunks they were
given, to detect two distinct failure modes:

1. FABRICATED citations — a [chunk_id] that doesn't exist in the
   research chunks at all. Zero-cost, zero-ambiguity check.
2. UNSUPPORTED claims — a real citation, but the surrounding claim
   isn't well-supported by that chunk's actual text. Approximate,
   word-overlap based (cheap) rather than LLM-based (would add real
   cost per verification — noted as a possible upgrade, not built here).
"""
import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

CITATION_PATTERN = re.compile(r"\[([A-Z0-9_\-]+_\d{4}-\d{2}-\d{2}_[A-Z0-9]+_\d+)\]")


@dataclass
class CitationCheck:
    chunk_id: str
    exists: bool
    support_score: float | None = None  # None if chunk didn't exist, so scoring is meaningless


@dataclass
class VerificationReport:
    total_citations: int
    fabricated_count: int
    low_support_count: int  # exists, but word-overlap support is weak
    checks: list[CitationCheck] = field(default_factory=list)

    @property
    def fabrication_rate(self) -> float:
        return self.fabricated_count / self.total_citations if self.total_citations else 0.0

    @property
    def trust_score(self) -> float:
        """
        Simple composite score (0-1): penalizes fabricated citations heavily
        (they're unambiguous failures), penalizes low-support ones moderately
        (they're approximate/fuzzy failures). Higher = more trustworthy.
        """
        if self.total_citations == 0:
            return 0.0  # no citations at all is itself a red flag for a grounded-answer system
        penalty = (self.fabricated_count * 1.0 + self.low_support_count * 0.5) / self.total_citations
        return max(0.0, 1.0 - penalty)


def _word_overlap_score(claim_text: str, source_text: str) -> float:
    """
    Cheap, free approximation of "is this claim supported by this source":
    fraction of the claim's significant words that also appear in the source.
    Not semantic understanding — just a fast, zero-cost sanity signal.
    """
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "and", "or", "of", "to", "in", "for", "on", "that", "this", "with", "as", "by"}
    claim_words = {w.lower().strip(".,;:") for w in claim_text.split() if w.lower() not in stopwords and len(w) > 2}
    source_words = {w.lower().strip(".,;:") for w in source_text.split()}

    if not claim_words:
        return 1.0
    overlap = claim_words & source_words
    return len(overlap) / len(claim_words)


def verify_citations(agent_text: str, research_chunks: list[dict]) -> VerificationReport:
    """
    Scans agent-generated text for [chunk_id] citations, checks each one
    exists in the actual retrieved chunks, and scores rough textual support
    for the sentence surrounding each citation.
    """
    chunk_lookup = {c["chunk_id"]: c["text"] for c in research_chunks}

    citations_found = CITATION_PATTERN.findall(agent_text)
    checks: list[CitationCheck] = []
    fabricated_count = 0
    low_support_count = 0

    for chunk_id in citations_found:
        exists = chunk_id in chunk_lookup

        if not exists:
            fabricated_count += 1
            checks.append(CitationCheck(chunk_id=chunk_id, exists=False))
            continue

        # Find the sentence containing this citation for a rough support check
        citation_marker = f"[{chunk_id}]"
        marker_pos = agent_text.find(citation_marker)
        sentence_start = agent_text.rfind(".", 0, marker_pos) + 1
        sentence_end = agent_text.find(".", marker_pos)
        claim_sentence = agent_text[sentence_start:sentence_end if sentence_end != -1 else marker_pos].strip()

        support = _word_overlap_score(claim_sentence, chunk_lookup[chunk_id])
        if support < 0.3:  # threshold: below this, the claim barely shares vocabulary with its cited source
            low_support_count += 1

        checks.append(CitationCheck(chunk_id=chunk_id, exists=True, support_score=support))

    report = VerificationReport(
        total_citations=len(citations_found),
        fabricated_count=fabricated_count,
        low_support_count=low_support_count,
        checks=checks,
    )
    logger.info(
        f"Citation check: {report.total_citations} citations, "
        f"{fabricated_count} fabricated, {low_support_count} low-support, "
        f"trust_score={report.trust_score:.2f}"
    )
    return report