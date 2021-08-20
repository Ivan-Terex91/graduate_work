from django.db import models
from django.utils.translation import gettext_lazy as _

import uuid


class Subscription(models.Model):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4)
    name = models.TextField(_('name'), null=False, blank=False)
    period = models.DurationField(_('period'), null=False, blank=False)


class SubscriptionFilm(models.Model):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4)
    sub_id = models.ForeignKey(verbose_name=_('sub_id'), to='Subscription', on_delete=models.CASCADE)
    film_id = models.TextField(_('film_id'), null=False, blank=False)
