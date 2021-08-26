import os

from core.settings import DatabaseSettings

PROJECT_NAME = "Billing API"
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8001/")

TORTOISE_CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": DatabaseSettings().dict(by_alias=True),
        },
    },
    "apps": {
        "billing": {
            "models": ["models.models"],
        }
    },
    "use_tz": True,
    "timezone": "Europe/Moscow",
}