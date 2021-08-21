from django.db import models
from django.utils.translation import gettext_lazy as _

import uuid


class Sub(models.Model):
    id = models.TextField(_('id'), primary_key=True, default=uuid.uuid4)
    name = models.TextField(_('name'), null=False, blank=False)
    period = models.DurationField(_('period'), null=False, blank=False)
    price = models.BigIntegerField(verbose_name=_('price'), null=False, blank=False)

    class Meta:
        managed = False
        verbose_name = _('subscription')
        verbose_name_plural = _('subscriptions')
        db_table = '"subscription"."sub"'

    def __str__(self):
        return self.name


class Sub_film_work(models.Model):
    id = models.TextField(_('id'), primary_key=True, default=uuid.uuid4)
    sub = models.ForeignKey(verbose_name=_('sub'), to='Sub', on_delete=models.CASCADE)
    film = models.ForeignKey(verbose_name=_('film'), to='movies.FilmWork', on_delete=models.CASCADE)

    class Meta:
        managed = False
        verbose_name = _('sub_film_work')
        verbose_name_plural = _('sub_film_works')
        db_table = '"subscription"."sub_film_work"'


class OrderType(models.TextChoices):
    IN_PROGRESS = 'in_progress', _('in_progress')
    PAID = 'paid', _('paid')


class Order(models.Model):
    id = models.TextField(_('id'), primary_key=True, default=uuid.uuid4)
    user_id = models.TextField(_('user_id'), null=False, blank=False)
    sub = models.ForeignKey(verbose_name=_('sub_id'), to='Sub', on_delete=models.CASCADE)
    type = models.TextField(_('type'), choices=OrderType.choices, null=False, blank=False)
    payment_method = models.TextField(_('payment_method'), null=False, blank=False)

    class Meta:
        managed = False
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        db_table = '"subscription"."order"'