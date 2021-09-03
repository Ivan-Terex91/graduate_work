import logging

from pydantic import BaseSettings, Field

logging.basicConfig(level=logging.INFO)


class Settings(BaseSettings):
    BILLING_API_URL: str = Field("http://localhost:8008", env="BILLING_API_URL")
    BILLING_API_BASE_ENDPOINT: str = Field(
        "/api/v1/billing", env="BILLING_API_BASE_ENDPOINT"
    )
