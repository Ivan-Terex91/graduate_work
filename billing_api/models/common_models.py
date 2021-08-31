from datetime import date
from enum import Enum, IntEnum
from typing import Optional

from pydantic import BaseModel, UUID4


class SubscriptionPeriod(IntEnum):
    """Периоды подписки"""

    WEEK = 7
    MONTH = 30
    SIX_MONTH = 180
    YEAR = 365


class SubscriptionType(Enum):
    """Тип подписки"""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


class Currency(Enum):
    """Валюты"""

    USD = "usd"
    RUB = "rub"


class SubscriptionState(Enum):
    """Статусы подписок"""

    CANCELED = "canceled"
    PAID = "paid"
    ACTIVE = "active"
    INACTIVE = "inactive"


class PaymentSystem(Enum):
    """Платёжные системы"""

    STRIPE = "stripe"
    YOOMONEY = "yoomoney"
    CLOUDPAYMENTS = "cloudpayments"


class OrderStatus(Enum):
    """Статусы заказа"""

    CREATED = "created"
    PROGRESS = "progress"
    PAID = "paid"
    ERROR = "error"


class PaymentInner(BaseModel):
    """Внутренняя модель платежа"""
    id: str
    amount: int


class RefundInner(BaseModel):
    """Внутренняя модель возврата"""
    id: str
    amount: str


class AuthUserInner(BaseModel):
    """Внутренняя модель авторизованного пользователя"""
    user_id: UUID4
    user_email: str
    first_name: Optional[str]
    last_name: Optional[str]
    birthdate: Optional[date]
    country: str
    user_roles: list[str]
    user_permissions: list[str]


class CustomerInner(BaseModel):
    """Внутренняя модель покупателя"""
    id: str
    email: str
