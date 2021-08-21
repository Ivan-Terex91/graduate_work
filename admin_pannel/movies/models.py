import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class FilmWorkType(models.TextChoices):
    MOVIE = 'movie', _('film')
    SERIAL = 'serial', _('serial')


class FilmWork(models.Model):
    id = models.TextField(_('id'), primary_key=True, default=uuid.uuid4)
    title = models.TextField(_('title'))
    description = models.TextField(_('description'), blank=True, null=True)
    creation_date = models.DateField(_('creation date'), blank=True, null=True)
    certificate = models.TextField(_('certificate'), blank=True, null=True)
    file_path = models.TextField(_('file_path'), blank=True, null=True)
    rating = models.FloatField(_('rating'), blank=True, null=True,
                               validators=[MinValueValidator(0), MaxValueValidator(10)])
    type = models.TextField(_('type'), null=False, choices=FilmWorkType.choices)
    created_at = models.DateTimeField(_('creation data'), blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(_('update date'), blank=True, null=True, auto_now=True)

    genres = models.ManyToManyField(
        'Genre',
        through='GenreFilmWork',
        verbose_name=_('film genres'),
        related_name='film_work_genres',
    )

    persons = models.ManyToManyField(
        'Person',
        through='PersonFilmWork',
        verbose_name=_('persons, worked on film'),
        related_name='film_work_persons',
    )

    class Meta:
        managed = False
        verbose_name = _('film work')
        verbose_name_plural = _('film works')
        db_table = '"content"."film_work"'

    def __str__(self):
        return self.title


class Genre(models.Model):
    id = models.TextField(_('id'), primary_key=True, default=uuid.uuid4)
    name = models.TextField(_('genre name'))
    description = models.TextField(_('description'), blank=True, null=True)
    created_at = models.DateTimeField(_('creation data'), blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(_('update date'), blank=True, null=True, auto_now=True)

    class Meta:
        managed = False
        verbose_name = _('genre')
        verbose_name_plural = _('genres')
        db_table = '"content"."genre"'

    def __str__(self):
        return self.name


class GenreFilmWork(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4)
    film_work = models.ForeignKey(
        FilmWork,
        on_delete=models.CASCADE,
        verbose_name=_('film work id'),
        related_name='film_works_g',
        null=False,
    )
    genre = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE,
        verbose_name=_('genre id'),
        related_name='genres',
        null=False,
    )
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"content"."genre_film_work"'
        unique_together = (('film_work_id', 'genre_id'),)

    def __str__(self):
        return self.genre.name


class Person(models.Model):
    id = models.TextField(_('id'), primary_key=True, default=uuid.uuid4)
    name = models.TextField(_('name'))
    birth_date = models.DateField(_('date of birth'), blank=True, null=True)
    created_at = models.DateTimeField(_('creation date'), blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(_('update date'), blank=True, null=True, auto_now=True)

    class Meta:
        managed = False
        verbose_name = _('person')
        verbose_name_plural = _('people')
        db_table = '"content"."person"'

    @property
    def roles(self):
        return ', '.join({row.role for row in self.persons.all()})

    def __str__(self):
        return self.name


class RoleType(models.TextChoices):
    WRITER = 'writer', _('writer')
    ACTOR = 'actor', _('actor')
    DIRECTOR = 'director', _('director')


class PersonFilmWork(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4)

    film_work = models.ForeignKey(
        FilmWork,
        on_delete=models.CASCADE,
        verbose_name=_('film work id'),
        related_name='film_works_p',
        null=False,
    )

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        verbose_name=_('person id'),
        related_name='persons',
        null=False,
    )

    role = models.TextField(_('role'), null=False, choices=RoleType.choices)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"content"."person_film_work"'
        unique_together = (('film_work', 'person', 'role'),)

    def __str__(self):
        return self.person.name
