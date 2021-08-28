import os
from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel


class SubscriptionPeriod(models.IntegerChoices):
    """Периоды подписки"""

    WEEK = 7, _("7")
    MONTH = 30, _("30")
    SIX_MONTH = 180, _("180")
    YEAR = 365, _("365")


class SubscriptionType(models.TextChoices):
    """Тип подписки"""

    BRONZE = "bronze", _("Бронза")
    SILVER = "silver", _("Серебро")
    GOLD = "gold", _("Золото")


class Currency(models.TextChoices):
    """Валюты"""

    USD = "usd", _("usd")
    RUB = "rub", _("rub")


class Subscription(TimeStampedModel):
    """Подписки"""

    id = models.UUIDField(
        verbose_name=_("идентификатор"), primary_key=True, default=uuid4, editable=False
    )
    title = models.CharField(
        verbose_name=_("название"), max_length=255, null=False, blank=False
    )
    description = models.TextField(verbose_name=_("описание"))
    period = models.PositiveIntegerField(
        verbose_name=_("период (кол-во дней)"),
        choices=SubscriptionPeriod.choices,
        null=False,
        blank=False,
    )
    type = models.CharField(
        verbose_name=_("тип подписки"),
        max_length=10,
        choices=SubscriptionType.choices,
        null=False,
        blank=False,
    )
    price = models.DecimalField(
        verbose_name=_("цена"), max_digits=10, decimal_places=2, null=False, blank=False
    )
    currency = models.CharField(
        verbose_name=_("валюта"),
        max_length=10,
        choices=Currency.choices,
        null=False,
        blank=False,
    )

    automatic = models.BooleanField(verbose_name=_("автоматическая"), default=False, null=False, blank=False)

    class Meta:
        verbose_name = _("подписка")
        verbose_name_plural = _("подписки")
        constraints = [
            models.UniqueConstraint(
                fields=["title", "period", "type"], name="subscription_unique"
            )
        ]
        db_table = f'"{os.getenv("BILLING_SCHEMA")}"."billing_subscription"'

    def __str__(self):
        return f"{self.title} - {self.type} - {self.period}"


class SubscriptionMovie(TimeStampedModel):
    """Фильмы в подписке"""

    id = models.UUIDField(
        verbose_name=_("идентификатор"), primary_key=True, default=uuid4, editable=False
    )
    subscription = models.ForeignKey(
        verbose_name=_("подписка"), to="Subscription", on_delete=models.CASCADE
    )
    movie = models.ForeignKey(
        verbose_name=_("кинопроизведение"), to="movies.Movie", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("фильм в подписке")
        verbose_name_plural = _("фильмы в подписке")
        db_table = f'"{os.getenv("BILLING_SCHEMA")}"."billing_subscriptionmovie"'

    def __str__(self):
        return f"{self.subscription} - {self.movie}"


class SubscriptionState(models.TextChoices):
    """Модель статусов подписок"""

    CANCELED = "canceled", _("Отменена")
    PAID = "paid", _("Оплачена")
    ACTIVE = "active", _("Активна")
    INACTIVE = "inactive", _("Неактивна")


class UsersSubscription(TimeStampedModel):
    """Подписки клиентов"""

    id = models.UUIDField(
        verbose_name=_("идентификатор"), primary_key=True, default=uuid4, editable=False
    )
    user_id = models.UUIDField(
        verbose_name=_("идентификатор клиента"), null=False, blank=False
    )
    subscription = models.ForeignKey(
        verbose_name=_("подписка"), to="Subscription", on_delete=models.RESTRICT
    )

    start_date = models.DateField(
        verbose_name=_("дата начала"), null=False, blank=False
    )
    end_date = models.DateField(
        verbose_name=_("дата окончания"), null=False, blank=False
    )

    status = models.CharField(
        verbose_name=_("статус"),
        max_length=20,
        choices=SubscriptionState.choices,
        default=SubscriptionState.INACTIVE,
        null=False,
        blank=False,
    )

    class Meta:
        verbose_name = _("подписка клиента")
        verbose_name_plural = _("Подписки клиентов")
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "subscription", "start_date", "end_date"], name="user_subscription_unique"
            )
        ]
        db_table = f'"{os.getenv("BILLING_SCHEMA")}"."billing_userssubscription"'

    def __str__(self):
        return f"{self.user_id} - {self.subscription} - {self.start_date}:{self.end_date}"


class PaymentSystem(models.TextChoices):
    """Платёжные системы"""

    STRIPE = "stripe"
    YOOMONEY = "yoomoney"
    CLOUDPAYMENTS = "cloudpayments"


# class PaymentMethod(TimeStampedModel):
#     """Способы оплаты"""
#
#     id = models.UUIDField(
#         verbose_name=_("идентификатор"), primary_key=True, default=uuid4, editable=False
#     )
#     payment_system = models.CharField(
#         verbose_name=_("платёжная система"),
#         max_length=20,
#         choices=PaymentSystem.choices,
#         default=PaymentSystem.STRIPE,
#         null=False,
#         blank=False,
#     )
#     type = models.CharField(verbose_name=_("тип"), max_length=50, null=False, blank=False)
#
#     def __str__(self):
#         return f"{self.payment_system} - {self.type}"
#
#     class Meta:
#         verbose_name = _("cпособ оплаты")
#         verbose_name_plural = _("cпособы оплаты")
#         db_table = f'"{os.getenv("BILLING_SCHEMA")}"."billing_paymentmethod"'


class OrderStatus(models.TextChoices):
    """Статусы заказа"""

    CREATED = "created", _("создан")
    PROGRESS = "progress", _("в обработке")
    PAID = "paid", _("оплачен")
    ERROR = "error", _("ошибка")


class Order(TimeStampedModel):
    """Заказы"""

    id = models.UUIDField(
        verbose_name=_("идентификатор"), primary_key=True, default=uuid4, editable=False
    )
    external_id = models.CharField(verbose_name=_("внешний идентификатор"), max_length=40, unique=True, null=False,
                                   blank=False)
    user_id = models.UUIDField(
        verbose_name=_("идентификатор клиента"), null=False, blank=False
    )
    user_email = models.EmailField(
        verbose_name=_("почта клиента"), max_length=50, null=False, blank=False
    )
    subscription = models.ForeignKey(
        verbose_name=_("подписка"), to="Subscription", on_delete=models.RESTRICT
    )
    status = models.CharField(
        verbose_name=_("статус заказа"),
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.CREATED,
        null=False,
        blank=False,
    )
    # payment_method = models.ForeignKey(
    #     verbose_name=_("способ оплаты"),
    #     to="PaymentMethod",
    #     on_delete=models.RESTRICT,
    #     null=False,
    #     blank=False,
    # )
    payment_system = models.CharField(verbose_name=_("Платёжная система"), max_length=20, choices=PaymentSystem.choices,
                                      default=PaymentSystem.STRIPE)
    currency = models.CharField(
        verbose_name=_("валюта"),
        max_length=10,
        choices=Currency.choices,
        null=False,
        blank=False,
    )
    discount = models.PositiveSmallIntegerField(verbose_name=_("скидка (%)"), default=0, null=False,
                                                blank=False)
    total_cost = models.DecimalField(
        verbose_name=_("итоговая стоимость"),
        max_digits=10,
        decimal_places=2,
        null=False,
        blank=False,
    )
    refund = models.BooleanField(verbose_name=_("возврат"), default=False)

    class Meta:
        verbose_name = _("заказ")
        verbose_name_plural = _("заказы")
        db_table = f'"{os.getenv("BILLING_SCHEMA")}"."billing_order"'

    def __str__(self):
        return f"{self.id} - {self.user_id} - {self.total_cost} - {self.status}"
