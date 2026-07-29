"""
Wraps Neo4j for storing and querying entity relationships extracted
from SEC filings.
"""
import os
import logging

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class GraphStore:
    def __init__(self) -> None:
        uri = os.environ["NEO4J_URI"]
        user = os.environ["NEO4J_USERNAME"]
        password = os.environ["NEO4J_PASSWORD"]
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self.driver.close()

    def add_company(self, ticker: str, filing_date: str) -> None:
        with self.driver.session() as session:
            session.run(
                "MERGE (c:Company {ticker: $ticker}) "
                "SET c.last_filing_date = $filing_date",
                ticker=ticker, filing_date=filing_date,
            )

    def add_competitor_relationship(self, ticker: str, competitor_name: str, source_chunk_id: str) -> None:
        with self.driver.session() as session:
            session.run(
                "MERGE (c:Company {ticker: $ticker}) "
                "MERGE (r:Competitor {name: $competitor_name}) "
                "MERGE (c)-[rel:COMPETES_WITH]->(r) "
                "SET rel.source_chunk_id = $source_chunk_id",
                ticker=ticker, competitor_name=competitor_name, source_chunk_id=source_chunk_id,
            )

    def add_risk_category(self, ticker: str, risk_category: str, source_chunk_id: str) -> None:
        with self.driver.session() as session:
            session.run(
                "MERGE (c:Company {ticker: $ticker}) "
                "MERGE (rk:RiskCategory {name: $risk_category}) "
                "MERGE (c)-[rel:HAS_RISK]->(rk) "
                "SET rel.source_chunk_id = $source_chunk_id",
                ticker=ticker, risk_category=risk_category, source_chunk_id=source_chunk_id,
            )

    def get_competitors(self, ticker: str) -> list[str]:
        with self.driver.session() as session:
            result = session.run(
                "MATCH (c:Company {ticker: $ticker})-[:COMPETES_WITH]->(r:Competitor) "
                "RETURN r.name AS name",
                ticker=ticker,
            )
            return [record["name"] for record in result]

    def get_shared_risks(self, ticker_a: str, ticker_b: str) -> list[str]:
        """The actual multi-hop query pure vector search can't do."""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (a:Company {ticker: $ticker_a})-[:HAS_RISK]->(rk:RiskCategory)"
                "<-[:HAS_RISK]-(b:Company {ticker: $ticker_b}) "
                "RETURN rk.name AS risk",
                ticker_a=ticker_a, ticker_b=ticker_b,
            )
            return [record["risk"] for record in result]