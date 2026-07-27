"""
Downloads a filing document from SEC EDGAR and converts it from raw HTML
into clean, readable plain text.

Design note: we keep this class separate from EdgarClient on purpose —
EdgarClient's job is "find the right URL," this class's job is "turn a URL
into usable text." Single Responsibility Principle: each class has one
reason to change.
"""
import logging
import time
import re

import requests
from bs4 import BeautifulSoup

from app.config import settings

logger = logging.getLogger(__name__)


class DocumentParser:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.sec_user_agent})

    def download_raw_html(self, document_url: str) -> str:
        """Downloads the raw HTML of a filing document."""
        time.sleep(settings.sec_rate_limit_delay_seconds)  # respect rate limit
        logger.info(f"Downloading document from {document_url}")
        response = self.session.get(document_url)
        response.raise_for_status()
        return response.text

    def html_to_clean_text(self, raw_html: str) -> str:
        """
        Strips a raw 10-K HTML document down to plain, readable text.

        Modern SEC filings use Inline XBRL (iXBRL) — HTML with an invisible
        layer of machine-readable financial tags (e.g. <ix:header>) embedded
        for software to parse structured data. That layer is hidden from
        human readers via CSS but NOT hidden from a naive text extractor,
        so we must explicitly strip it out or it pollutes our clean text
        with taxonomy URLs and tag metadata instead of real sentences.
        """
        soup = BeautifulSoup(raw_html, "lxml")

        # Remove non-content elements
        for tag in soup(["script", "style", "head", "meta", "link"]):
            tag.decompose()

        # Remove iXBRL's hidden metadata block — this is where the
        # fasb.org taxonomy references were leaking in from
        for ix_header in soup.find_all(re.compile(r"^ix:header")):
            ix_header.decompose()

        # Remove any element explicitly hidden via inline CSS — iXBRL filings
        # commonly wrap their full tag dictionary in a display:none div
        for hidden in soup.find_all(style=re.compile(r"display:\s*none")):
            hidden.decompose()

        text = soup.get_text(separator="\n")

        lines = [line.strip() for line in text.splitlines()]
        non_empty_lines = [line for line in lines if line]
        clean_text = "\n".join(non_empty_lines)

        return clean_text