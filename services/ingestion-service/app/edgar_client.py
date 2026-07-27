"""
Client for interacting with SEC EDGAR's public APIs.

Two-step lookup pattern:
  1. Resolve a stock ticker (e.g. "AAPL") to SEC's internal CIK identifier
  2. Use the CIK to fetch that company's filing history and locate the
     most recent 10-K
"""
import time
import logging
from typing import Optional

import requests

from app.config import settings

logger = logging.getLogger(__name__)


class EdgarClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.sec_user_agent})
        self._ticker_to_cik: dict[str, str] = {}

    def _load_ticker_map(self) -> None:
        """Downloads SEC's ticker-to-CIK mapping file (cached in memory)."""
        if self._ticker_to_cik:
            return  # already loaded

        url = f"{settings.sec_base_url}/files/company_tickers.json"
        logger.info(f"Fetching ticker map from {url}")
        response = self.session.get(url)
        response.raise_for_status()

        data = response.json()
        # SEC returns CIK without leading zeros; the submissions API wants
        # a 10-digit zero-padded string, so we normalize it here.
        for entry in data.values():
            ticker = entry["ticker"].upper()
            cik = str(entry["cik_str"]).zfill(10)
            self._ticker_to_cik[ticker] = cik

    def get_cik(self, ticker: str) -> Optional[str]:
        """Resolves a ticker symbol (e.g. 'AAPL') to its CIK."""
        self._load_ticker_map()
        return self._ticker_to_cik.get(ticker.upper())

    def get_latest_10k(self, ticker: str) -> Optional[dict]:
        """
        Fetches metadata for a company's most recent 10-K filing.
        Returns None if the ticker isn't found or has no 10-K on record.
        """
        cik = self.get_cik(ticker)
        if not cik:
            logger.warning(f"No CIK found for ticker: {ticker}")
            return None

        time.sleep(settings.sec_rate_limit_delay_seconds)  # respect rate limit

        url = f"{settings.sec_data_url}/submissions/CIK{cik}.json"
        logger.info(f"Fetching filing history for CIK {cik} ({ticker})")
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()

        recent = data["filings"]["recent"]
        for i, form_type in enumerate(recent["form"]):
            if form_type == "10-K":
                accession_number = recent["accessionNumber"][i].replace("-", "")
                primary_doc = recent["primaryDocument"][i]
                filing_date = recent["filingDate"][i]

                doc_url = (
                    f"{settings.sec_base_url}/Archives/edgar/data/"
                    f"{int(cik)}/{accession_number}/{primary_doc}"
                )
                return {
                    "ticker": ticker.upper(),
                    "cik": cik,
                    "filing_date": filing_date,
                    "document_url": doc_url,
                }

        logger.warning(f"No 10-K found in recent filings for {ticker}")
        return None