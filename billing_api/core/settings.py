from pydantic import BaseSettings, Field


class DatabaseSettings(BaseSettings):
    """Настройки для postgres"""
    host: str = Field("localhost", env="POSTGRES_HOST")
    port: int = Field(5432, env="POSTGRES_PORT")
    user: str = Field("postgres", env="POSTGRES_USER")
    password: str = Field("postgres", env="POSTGRES_PASSWORD")
    database: str = Field("movies", env="POSTGRES_DB")
    scheme: str = Field("billing", env="BILLING_SCHEMA", alias="schema")
