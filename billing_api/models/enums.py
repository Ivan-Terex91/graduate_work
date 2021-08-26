from enum import Enum, IntEnum


class SubscriptionPeriod(IntEnum):
    """Периоды подписки"""

    THIRTY_DAYS = 30
    NINETY_DAYS = 90
    ONE_HUNDRED_AND_EIGHTY_DAYS = 180


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
