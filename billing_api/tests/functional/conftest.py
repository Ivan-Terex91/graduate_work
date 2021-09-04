import asyncio
import os
from datetime import datetime

import aiohttp
import httpx
import psycopg2
import pytest
from pydantic import AnyHttpUrl, BaseSettings

pg_dsn = {
    "dbname": os.environ.get("POSTGRES_DB", "movies"),
    "user": os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("POSTGRES_PASSWORD", "postgres"),
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": int(os.environ.get("POSTGRES_PORT", 5432)),
}


class Settings(BaseSettings):
    """Класс с тестовыми настройками"""

    auth_url: AnyHttpUrl = "http://localhost:8001/"  # TODO env
    billing_api_url: AnyHttpUrl = "http://localhost:8008/"  # TODO env

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings():
    return Settings()


@pytest.fixture(scope="session")
async def http_session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest.fixture(scope="session")
async def add_subscription(settings):
    with psycopg2.connect(**pg_dsn) as conn:
        cursor = conn.cursor()
        # cursor.execute("""
        # DELETE FROM billing.billing_subscription
        # """)
        cursor.execute(
            """
        INSERT INTO billing.billing_subscription 
        (id, title, description, period, type, price, currency, automatic, created, modified)
        VALUES ('4e7c09ff-f69e-45f0-8285-99f80a289320', 'Подписка', 'Описание', 30, 'bronze', 100, 'usd', false, 
        NOW(), NOW());"""
        )


# TODO тут будет фикстура очистки БД


@pytest.fixture(scope="session")
async def get_auth_user(
    settings: Settings, http_session: aiohttp.ClientSession, add_subscription
):
    user_data = {
        "email": f"{int(datetime.timestamp(datetime.now()))}@mail.ru",
        "password": "password",
    }
    async with httpx.AsyncClient(base_url=settings.auth_url) as client:
        signup_user = await client.post(url="api/v1/auth/signup/", json=user_data)

        tokes = await client.post(url="api/v1/auth/login/", json=user_data)
        tokes = tokes.json()
        user_profile_data = await client.get(
            url="api/v1/profile/", headers={"TOKEN": f"{tokes['access_token']}"}
        )
        user_profile_data = user_profile_data.json()
        user_profile_data.update(tokes)
        return user_profile_data
