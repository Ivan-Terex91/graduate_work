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
            "models": ["models.db_models"],
        }
    },
    "use_tz": True,
    "timezone": "Europe/Moscow",
}

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "STRIPE_API_KEY")
STRIPE_BASE_URL = os.getenv("STRIPE_BASE_URL", "https://api.stripe.com/v1")
