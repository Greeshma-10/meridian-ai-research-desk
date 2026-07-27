"""
Configuration for the ingestion service.

We use pydantic-settings so config can come from environment variables
(12-factor app principle) instead of being hardcoded — this is what lets
the same code run identically in dev, CI, and production.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # SEC REQUIRES a descriptive User-Agent identifying the requester.
    # Format: "Company/App Name (contact@email.com)"
    # Requests without this get blocked — this is not optional.
    sec_user_agent: str = "Meridian-AI-Research (gree.unofficial21@gmail.com)"
    sec_base_url: str = "https://www.sec.gov"
    sec_data_url: str = "https://data.sec.gov"

    # SEC's rate limit guidance: stay under 10 requests/second
    sec_rate_limit_delay_seconds: float = 0.15


settings = Settings()