import asyncio
from datetime import datetime

import pytest
from billing_api.core.stripe import StripeClient

from .settings import TEST_STRIPE_API_KEY, TEST_STRIPE_BASE_URL


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_payment_method_data():
    payment_method_data = {
        "type": "card",
        "card_number": "4242424242424242",
        "card_exp_month": 9,
        "card_exp_year": 2022,
        "card_cvc": "314",
    }

    yield payment_method_data


@pytest.fixture(scope="function")
async def test_user_data():
    user_data = {
        "user_id": "4e7c09ff-f69e-45f0-8285-99f80a289320",
        "user_email": f"{int(datetime.timestamp(datetime.now()))}@mail.ru",
    }
    yield user_data


@pytest.fixture(scope="session")
async def test_stripe_client():
    yield StripeClient(url=TEST_STRIPE_BASE_URL, api_key=TEST_STRIPE_API_KEY)
