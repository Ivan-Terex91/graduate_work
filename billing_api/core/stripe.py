import logging

import backoff
import stripe
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientError
from pydantic import UUID4

from models.api_models import PaymentMethodData, PaymentMethodDataOut
from models.common_models import CustomerInner, PaymentInner, RefundInner

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
        payment_method_id: str,
    ) -> PaymentInner:
        """Создание платежа"""
        payment_intent_data = {
            "customer": customer_id,
            "amount": amount,
            "currency": currency,
            "receipt_email": user_email,
            "payment_method": payment_method_id,
        }
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
        payment_method_id: str,
    ) -> PaymentInner:
        """Создание рекурентного платежа"""
        payment_intent_data = {
            "customer": customer_id,
            "amount": amount,
            "currency": currency,
            "receipt_email": user_email,
            "payment_method": payment_method_id,
            "confirm": True,
            "off_session": True,
        }
        payment = await self._request(
            method="POST", endpoint="/payment_intents", data=payment_intent_data
        )
        return PaymentInner(**payment)

    async def confirm_payment(self, payment_id: str, payment_method: str):
        """Подтверждение платёжа"""
        data = {"payment_method": payment_method}
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

    async def create_refund(self, payment_intent_id: str, amount: int) -> RefundInner:
        """Создание возврата"""
        data = {"payment_intent": payment_intent_id, "amount": amount}
        refund = await self._request(method="POST", endpoint="/refunds", data=data)
        print(refund)
        return RefundInner(**refund)

    async def get_refund_data(self, refund_order_id: str) -> RefundInner:
        """Получение данных о возврате"""
        refund = await self._request(
            method="GET", endpoint=f"/refunds/{refund_order_id}"
        )
        return RefundInner(**refund)

    async def create_payment_method(
        self, payment_method_data: PaymentMethodData
    ) -> PaymentMethodDataOut:
        """Создание платёжного метода"""
        data = {
            "type": payment_method_data.type.value,
            "card[number]": payment_method_data.card_number,
            "card[exp_month]": payment_method_data.card_exp_month,
            "card[exp_year]": payment_method_data.card_exp_year,
            "card[cvc]": payment_method_data.card_cvc,
        }
        method = await self._request(
            method="POST", endpoint="/payment_methods", data=data
        )
        return PaymentMethodDataOut(id=method.get("id"), type=payment_method_data.type)

    async def attach_payment_method(
        self, payment_method_id: str, customer_id: str
    ) -> None:
        data = {"customer": customer_id}
        """Прикрепление платёжного метода к покупателю(клиенту)"""
        await self._request(
            method="POST",
            endpoint=f"/payment_methods/{payment_method_id}/attach",
            data=data,
        )


async def get_stripe() -> StripeClient:
    return StripeClient(url=STRIPE_BASE_URL, api_key=STRIPE_API_KEY)
