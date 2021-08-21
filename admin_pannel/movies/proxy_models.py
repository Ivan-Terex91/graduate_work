from django.db import models
from django.utils.translation import gettext_lazy as _

from .models import FilmWork


class FilmWorkFilterManager(models.Manager):
    def __init__(self, film_work_type: str):
        super(FilmWorkFilterManager, self).__init__()
        self.film_work_type = film_work_type

    def get_queryset(self):
        return super().get_queryset().filter(type=self.film_work_type)


class Movie(FilmWork):
    objects = FilmWorkFilterManager('movie')

    def save(self, *args, **kwargs):
        self.type = 'movie'
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        managed = False
        verbose_name = _('movie')
        verbose_name_plural = _('movies')


class Serial(FilmWork):
    objects = FilmWorkFilterManager('serial')

    def save(self, *args, **kwargs):
        self.type = 'serial'
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        managed = False
        verbose_name = _('serial')
        verbose_name_plural = _('serials')
