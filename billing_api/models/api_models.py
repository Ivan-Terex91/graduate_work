import datetime
from typing import Optional

from pydantic import UUID4, BaseModel, Field

from models.common_models import (
    Currency,
    OrderStatus,
    PaymentSystem,
    SubscriptionPeriod,
    SubscriptionState,
    SubscriptionType,
)


class SubscriptionApiModel(BaseModel):
    """Подписка"""

    title: str
    description: str
    period: SubscriptionPeriod
    type: SubscriptionType
    price: float
    currency: Currency
    automatic: bool


class UserSubscriptionApiModel(BaseModel):
    """Подпиcка пользователя"""

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
    total_cost: float
    refund: bool


class PaymentDataIn(BaseModel):
    """Входные данные для оплаты подписки"""
    subscription_id: UUID4
    payment_system: PaymentSystem
    currency: Currency
    discount: int = Field(ge=0, le=99)
    total_cost: float
    # TODO можно включить цену, валюту, но можно взять и через id это. Плюс открытый вопрос с payment method


class RefundDataIn(BaseModel):
    """Входные данные для возврата денег за подписку"""
    subscription_id: UUID4
