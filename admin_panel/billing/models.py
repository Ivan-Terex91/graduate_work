import os

from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from uuid import uuid4


class SubscriptionPeriod(models.IntegerChoices):
    """Периоды подписки"""
    THIRTY_DAYS = 30, _("30")
    NINETY_DAYS = 90, _("90")
    ONE_HUNDRED_AND_EIGHTY_DAYS = 180, _("180")


class Currency(models.TextChoices):
    """Валюты"""
    USD = "usd", _("usd")
    RUB = "rub", _("rub")


class Subscription(TimeStampedModel):
    """Подписки"""
    id = models.UUIDField(verbose_name=_('идентификатор'), primary_key=True, default=uuid4, editable=False)
    name = models.CharField(verbose_name=_('название'), max_length=255, null=False, blank=False)
    period = models.PositiveIntegerField(verbose_name=_('период(кол-во дней)'), choices=SubscriptionPeriod.choices,
                                         null=False,
                                         blank=False)
    product = models.ForeignKey(verbose_name=_('продукт'), to='Product', on_delete=models.RESTRICT)

    class Meta:
        verbose_name = _('подписка')
        verbose_name_plural = _('подписки')
        constraints = [
            models.UniqueConstraint(fields=['name', 'period'], name='subscription_unique')
        ]
        db_table = f'"{os.getenv("BILLING_SCHEMA")}"."billing_subscription"'

    def __str__(self):
        return f'{self.name} - {self.period}'


class SubscriptionMovie(TimeStampedModel):
    """Фильмы в подписке"""
    id = models.UUIDField(verbose_name=_('идентификатор'), primary_key=True, default=uuid4, editable=False)
    subscription = models.ForeignKey(verbose_name=_('подписка'), to='Subscription', on_delete=models.CASCADE)
    movie = models.ForeignKey(verbose_name=_('кинопроизведение'), to='movies.Movie', on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('фильм в подписке')
        verbose_name_plural = _('фильмы в подписке')
        db_table = f'"{os.getenv("BILLING_SCHEMA")}"."billing_subscriptionmovie"'

    def __str__(self):
        return f'{self.subscription} - {self.movie}'


class Product(models.Model):
    """Продукты"""
    id = models.UUIDField(verbose_name=_('идентификатор'), primary_key=True, default=uuid4, editable=False)
    name = models.CharField(verbose_name=_('наименование'), max_length=255, null=False, blank=False)
    description = models.TextField(verbose_name=_('описание'))
    price = models.DecimalField(verbose_name=_('цена'), max_digits=10, decimal_places=2, null=False, blank=False)
    currency = models.CharField(verbose_name=_('валюта'), max_length=10, choices=Currency.choices, null=False,
                                blank=False)

    class Meta:
        verbose_name = _('продукт')
        verbose_name_plural = _('продукты')
        db_table = f'"{os.getenv("BILLING_SCHEMA")}"."billing_product"'

    def __str__(self):
        return f'{self.name} - {self.price}'


class OrderStatus(models.TextChoices):
    """Статусы заказа"""
    CREATED = 'created', _('создан')
    PROGRESS = 'progress', _('в обработке')
    PAID = 'paid', _('оплачен')
    ERROR = 'error', _('ошибка')


class Order(TimeStampedModel):
    """Заказы"""
    id = models.UUIDField(verbose_name=_('идентификатор'), primary_key=True, default=uuid4, editable=False)
    user_id = models.UUIDField(verbose_name=_('идентификатор клиента'), null=False, blank=False)
    product = models.ForeignKey(verbose_name=_('продукт'), to='Product', on_delete=models.RESTRICT)
    status = models.CharField(verbose_name=_('статус'), max_length=20, choices=OrderStatus.choices, null=False,
                              blank=False)
    payment_method = models.TextField(verbose_name=_('способ оплаты'), null=False, blank=False)

    class Meta:
        verbose_name = _('заказ')
        verbose_name_plural = _('заказы')
        db_table = f'"{os.getenv("BILLING_SCHEMA")}"."billing_order"'
