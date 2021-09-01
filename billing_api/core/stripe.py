import logging

import backoff
import stripe
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientError
from models.common_models import CustomerInner, PaymentInner, RefundInner
from pydantic import UUID4

from .config import STRIPE_API_KEY, STRIPE_BASE_URL

logger = logging.getLogger(__name__)


class StripeClient:
    """Клиент для stripe"""

    def __init__(self, url: str, api_key: str):
        self.client = stripe
        self.base_url = url
        self.api_key = api_key
        self.auth_header = {
            "Authorization": f"Bearer {self.api_key}",
        }

    @backoff.on_exception(
        exception=ClientError, wait_gen=backoff.expo, max_time=30, logger=logger
    )
    async def _request(
        self, method: str, endpoint: str, headers: dict = None, data: dict = None
    ):
        async with ClientSession(headers=self.auth_header) as session:
            async with session.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                headers=headers,
                data=data,
            ) as resp:
                response = await resp.json()
                return response

    async def create_customer(self, user_id: UUID4, user_email: str) -> CustomerInner:
        """Создание покупателя(клиента)"""
        customer_data = {
            "id": str(user_id),
            "email": user_email,
        }

        response = await self._request(
            method="POST", endpoint="/customers", data=customer_data
        )

        if "error" in response:
            if response["error"]["code"] == "resource_already_exists":
                return CustomerInner(**customer_data)
        return CustomerInner(**response)

    async def create_payment(
        self,
        customer_id: str,
        amount: float,
        currency: str,
        user_email: str,
        # payment_method,
    ) -> PaymentInner:
        """Создание платежа"""
        # TODO setup_future_usage='off_session' или "off_session": True это параметр для внесессионных платежей,
        #  скорее всего для реализации автоматичесих списаний
        payment_intent_data = {
            "customer": customer_id,
            "amount": amount,
            "currency": currency,
            "receipt_email": user_email,
            "payment_method": "pm_card_visa",  # TODO с этим нужно доразобраться!!!!
        }  # TODO payment_method
        payment = await self._request(
            method="POST", endpoint="/payment_intents", data=payment_intent_data
        )
        return PaymentInner(**payment)

    async def create_recurrent_payment(
        self,
        customer_id: str,
        amount: float,
        currency: str,
        user_email: str,
        payment_method,
    ):
        """Создание рекурентного платежа"""
        # TODO setup_future_usage='off_session' или "off_session": True это параметр для внесессионных платежей,
        #  скорее всего для реализации автоматичесих списаний
        payment_intent_data = {
            "customer": customer_id,
            "amount": amount,
            "currency": currency,
            "receipt_email": user_email,
            "payment_method": "pm_card_visa",
        }  # TODO payment_method
        return await self._request(
            method="POST", endpoint="/payment_intents", data=payment_intent_data
        )

    async def confirm_payment(self, payment_id: str, payment_method: str = None):
        """Подтверждение платёжа"""
        # TODO как я понял, это симуляция метода подтверждения от пользователя по client_secret
        # data = {"payment_method": "pm_card_visa"}  # TODO данные карты и т.д.
        data = {"payment_method": "pm_card_visa"}
        return await self._request(
            method="POST",
            endpoint=f"/payment_intents/{payment_id}/confirm",
            data=data,
        )

    async def get_payment_data(self, payment_intents_id: str) -> PaymentInner:
        """Получение данных о платеже"""
        payment = await self._request(
            method="GET", endpoint=f"/payment_intents/{payment_intents_id}"
        )
        return PaymentInner(**payment)

    async def create_refund(self, payment_intent_id: str, amount: int):
        """Создание возврата"""
        data = {"payment_intent": payment_intent_id, "amount": amount}
        refund = await self._request(method="POST", endpoint="/refunds", data=data)
        return RefundInner(**refund)

    async def get_refund_data(self, refund_order_id: str) -> RefundInner:
        """Получение данных о возврате"""
        refund = await self._request(
            method="GET", endpoint=f"/refunds/{refund_order_id}"
        )
        print(refund)
        return RefundInner(**refund)


async def get_stripe() -> StripeClient:
    return StripeClient(url=STRIPE_BASE_URL, api_key=STRIPE_API_KEY)
