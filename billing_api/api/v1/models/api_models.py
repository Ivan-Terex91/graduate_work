import datetime

from pydantic import UUID4, BaseModel

from models.enums import (Currency, OrderStatus, PaymentSystem,
                          SubscriptionPeriod, SubscriptionState,
                          SubscriptionType)


class SubscriptionApiModel(BaseModel):
    """Подписка"""

    title: str
    description: str
    period: SubscriptionPeriod
    type: SubscriptionType
    price: float
    currency: Currency


class UserSubscriptionApiModel(BaseModel):
    """Подпиcка пользователя"""

    user_id: UUID4
    subscription: SubscriptionApiModel
    start_date: datetime.date
    end_date: datetime.date
    status: SubscriptionState


class PaymentMethodApiModel(BaseModel):
    """Способы оплаты"""

    payment_system: PaymentSystem
    type = str


class OrderApiModel(BaseModel):
    """Заказы"""

    user_id: UUID4
    user_email: str
    subscription: SubscriptionApiModel
    status: OrderStatus
    payment_method: PaymentMethodApiModel
    currency: Currency
    discount: int
    total_cost: float
