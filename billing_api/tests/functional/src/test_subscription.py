import httpx
import pytest
from billing_api.tests.functional.conftest import Settings


@pytest.mark.asyncio
class TestSubscription:
    """
    Класс для тест-кейса.
    1. Пользователь оформил подписку. Проверить в БД заказ, статус заказа
    2. Подтвердил оплату, Проверить в БД статус заказа, проверить наличие подписки, данные подписки, статус подписки
    3. Вернул деньги за подписку. Проверить в БД заказ на возврат, статус подписки.
    """

    async def test_create_payment_subscription(
        self, get_auth_user: dict, settings: Settings
    ):
        """Тест оформления подписки"""
        payment_data = {
            "subscription_id": "4e7c09ff-f69e-45f0-8285-99f80a289320",
            "payment_system": "stripe",
            "currency": "usd",
            "discount": 0,
            "total_cost": 100,
            "payment_method": {
                "type": "card",
                "card_number": "4242424242424242",
                "card_exp_month": 9,
                "card_exp_year": 2022,
                "card_cvc": "314",
            },
        }
        user = get_auth_user
        async with httpx.AsyncClient(
            base_url=settings.billing_api_url,
            headers={"TOKEN": f"{user['access_token']}"},
        ) as client:
            await client.post(
                "/api/v1/billing/subscription/payment/create", json=payment_data
            )
