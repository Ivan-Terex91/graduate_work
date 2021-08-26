from tortoise import fields
from tortoise.models import Model
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


class AbstractModel(Model):
    """Абстрактная модель с общими полями"""
    id = fields.UUIDField(pk=True)
    created = fields.DatetimeField()
    modified = fields.DatetimeField()

    class Meta:
        abstract = True


class Subscription(AbstractModel):
    """Подписки"""
    title = fields.CharField(max_length=255, null=False)
    description = fields.TextField()
    period: SubscriptionPeriod = fields.IntEnumField(enum_type=SubscriptionPeriod)
    type: SubscriptionType = fields.CharEnumField(enum_type=SubscriptionType)
    price = fields.DecimalField(max_digits=10, decimal_places=2, null=False)
    currency: Currency = fields.CharEnumField(enum_type=Currency)

    class Meta:
        table = "billing_subscription"

    def __str__(self):
        return f"{self.title} - {self.type} - {self.period}"


class UsersSubscription(AbstractModel):
    """Подписки клиентов"""

    user_id = fields.UUIDField(null=False)
    subscription: fields.ForeignKeyRelation[Subscription] = fields.ForeignKeyField("billing.Subscription",
                                                                                   on_delete=fields.RESTRICT
                                                                                   )
    start_date = fields.DateField(null=False)
    end_date = fields.DateField(null=False)
    status: SubscriptionState = fields.CharEnumField(enum_type=SubscriptionState)

    class Meta:
        table = "billing_userssubscription"

    def __str__(self):
        return f"{self.user_id} - {self.subscription} - {self.status}"


class PaymentMethod(AbstractModel):
    """Способы оплаты"""

    payment_system: PaymentSystem = fields.CharEnumField(enum_type=PaymentSystem, default=PaymentSystem.STRIPE)
    type = fields.CharField(max_length=50, null=False)

    class Meta:
        table = "billing_paymentmethod"

    def __str__(self):
        return f"{self.payment_system} - {self.type}"

    subscription: fields.ForeignKeyRelation[Subscription] = fields.ForeignKeyField("billing.Subscription",
                                                                                   on_delete=fields.RESTRICT
                                                                                   )


class Order(AbstractModel):
    """Заказы"""

    user_id = fields.UUIDField(null=False)
    user_email = fields.CharField(max_length=50, null=False)
    subscription: fields.ForeignKeyRelation[Subscription] = fields.ForeignKeyField("billing.Subscription",
                                                                                   on_delete=fields.RESTRICT
                                                                                   )
    status: OrderStatus = fields.CharEnumField(enum_type=OrderStatus, default=OrderStatus.CREATED)
    payment_method: fields.ForeignKeyRelation[PaymentMethod] = fields.ForeignKeyField("billing.PaymentMethod",
                                                                                      on_delete=fields.RESTRICT,
                                                                                      )
    currency: Currency = fields.CharEnumField(enum_type=Currency)
    discount = fields.SmallIntField(default=0, null=False)
    total_cost = fields.DecimalField(max_digits=10, decimal_places=2, null=False)

    class Meta:
        table = "billing_order"

    def __str__(self):
        return f"{self.id} - {self.user_id} - {self.total_cost} - {self.status}"
