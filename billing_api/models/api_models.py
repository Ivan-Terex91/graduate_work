import datetime
from decimal import Decimal
from typing import Optional

from models.common_models import (Currency, OrderStatus, PaymentSystem,
                                  SubscriptionPeriod, SubscriptionState,
                                  SubscriptionType, PaymentMethodType)

from pydantic import UUID4, BaseModel, Field


class SubscriptionApiModel(BaseModel):
    """Подписка"""
    # id: UUID4
    title: str
    description: str
    period: SubscriptionPeriod
    type: SubscriptionType
    price: Decimal
    currency: Currency
    automatic: bool


class UserSubscriptionApiModel(BaseModel):
    """Подпиcка пользователя"""
    # id: UUID4
    user_id: UUID4
    subscription: SubscriptionApiModel
    start_date: datetime.date
    end_date: datetime.date
    status: SubscriptionState


# class PaymentMethodApiModel(BaseModel):
#     """Способы оплаты"""
#
#     payment_system: PaymentSystem
#     type = str


class OrderApiModel(BaseModel):
    """Заказы"""

    external_id: Optional[str] = None
    user_id: UUID4
    user_email: str
    subscription: SubscriptionApiModel
    status: OrderStatus
    payment_system: PaymentSystem
    currency: Currency
    discount: int
    total_cost: Decimal
    refund: bool


class PaymentMethodData(BaseModel):
    """Модель для метода оплаты картой"""

    type: PaymentMethodType
    card_number: str = Field(min_length=16, max_length=16)
    card_exp_month: int = Field(ge=datetime.date.today().month, le=12)
    card_exp_year: int = Field(ge=datetime.date.today().year)
    card_cvc: str = Field(min_length=3, max_length=3)

    class Config:
        schema_extra = {
            "example": {
                "type": "card",
                "card_number": "4242424242424242",
                "card_exp_month": 9,
                "card_exp_year": 2022,
                "card_cvc": "314",
            }
        }


class PaymentMethodDataOut(BaseModel):
    """Модель платёжного метода из Stripe"""
    id: str
    type: PaymentMethodType


class PaymentDataIn(BaseModel):
    """Входные данные для оплаты подписки"""

    subscription_id: UUID4
    payment_system: PaymentSystem
    currency: Currency
    discount: int = Field(ge=0, le=99)
    total_cost: Decimal
    payment_method: PaymentMethodData
    # TODO можно включить цену, валюту, но можно взять и через id это. Плюс открытый вопрос с payment method


class RefundDataIn(BaseModel):
    """Входные данные для возврата денег за подписку"""

    subscription_id: UUID4


class ExpireUserSubscriptionData(BaseModel):
    user_id: UUID4
    subscription_id: UUID4
