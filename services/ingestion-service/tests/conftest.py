"""
Shared pytest fixtures — reusable test data available to every test file
in this directory without duplicating setup code.
"""
import pytest


@pytest.fixture
def sample_10k_text() -> str:
    """
    A minimal but realistic fake 10-K text, including a deliberate
    Table-of-Contents-style mention of 'Item 1A' BEFORE the real section —
    this is specifically designed to test the last-match-wins heuristic
    from Milestone 5.
    """
    return """UNITED STATES SECURITIES AND EXCHANGE COMMISSION
FORM 10-K

TABLE OF CONTENTS
Item 1. Business
Item 1A. Risk Factors
Item 7. Management's Discussion and Analysis

Item 1. Business
This is the real business section describing what the company does.
The company operates in multiple markets and has various products.

Item 1A. Risk Factors
This is the real risk factors section. The company faces competition
from various sources. Regulatory changes could impact operations.

Item 7. Management's Discussion and Analysis
This is the real MD&A section discussing financial performance and
results of operations for the fiscal year.
"""


@pytest.fixture
def messy_html_with_hidden_xbrl() -> str:
    """Simulates the exact iXBRL problem we hit in Milestone 4."""
    return """
    <html>
    <head><style>body { color: red; }</style></head>
    <body>
        <ix:header style="display:none">
            <div>http://fasb.org/us-gaap/2025#LongTermDebtNoncurrent</div>
        </ix:header>
        <div style="display:none">Hidden metadata that should be stripped</div>
        <p>UNITED STATES SECURITIES AND EXCHANGE COMMISSION</p>
        <p>Apple Inc.</p>
        <script>console.log('should be removed');</script>
    </body>
    </html>
    """