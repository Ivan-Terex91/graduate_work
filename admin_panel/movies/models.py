import os
from uuid import uuid4

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel


class MovieType(models.TextChoices):
    """Типы кинопроизведений."""
    movie = 'movie', _('фильм')
    serial = 'serial', _('сериал')
    tv_show = 'tv_show', _('шоу')
    cartoon = 'cartoon', _('мультфильм')


class Movie(TimeStampedModel):
    """Кинопроизведения."""
    id = models.UUIDField(_('идентификатор'), primary_key=True, default=uuid4, editable=False)
    title = models.CharField(_('название'), max_length=255)
    description = models.TextField(_('описание'), blank=True, null=True)
    creation_date = models.DateField(_('дата создания фильма'), blank=True, db_index=True)
    age_limit = models.PositiveSmallIntegerField(_('ограничение по возрасту'), validators=[MaxValueValidator(21)],
                                                 db_index=True)
    rating = models.FloatField(_('рейтинг пользователей'), blank=True, validators=[MinValueValidator(0)], db_index=True)
    imdb_rating = models.FloatField(_('IMDB рейтинг'), validators=[MinValueValidator(0)], db_index=True)
    movie_type = models.CharField(_('тип'), max_length=20, choices=MovieType.choices, db_index=True)
    file_path = models.FileField(_('файл'), upload_to='movie_files/', blank=True)
    genres = models.ManyToManyField('Genre', verbose_name=_('Жанры'), db_index=True)
    persons = models.ManyToManyField('Person', through='MoviePerson')

    class Meta:
        verbose_name = _('кинопроизведение')
        verbose_name_plural = _('кинопроизведения')

        constraints = [
            models.UniqueConstraint(fields=['title', 'creation_date'], name='movie_unique')
        ]
        db_table = f'"{os.getenv("MOVIES_SCHEMA", "content")}"."movies_movie"'

    def __str__(self):
        return self.title

    def clean(self):
        """Подстраховка на добавление фильмов с одинаковым названием."""
        self.title = self.title.capitalize()
        super().clean()


class Genre(TimeStampedModel):
    """Жанры."""
    id = models.UUIDField(_('идентификатор'), primary_key=True, default=uuid4, editable=False)
    name = models.CharField(_('название'), max_length=255, unique=True)
    description = models.TextField(_('описание'), blank=True, null=True)

    class Meta:
        verbose_name = _('жанр')
        verbose_name_plural = _('жанры')
        db_table = f'"{os.getenv("MOVIES_SCHEMA", "content")}"."movies_genre"'

    def __str__(self):
        return self.name

    def clean(self):
        """Подстраховка на добавление одинаковых жанров."""
        self.name = self.name.capitalize()
        super().clean()


class Person(TimeStampedModel):
    """Люди."""
    id = models.UUIDField(_('идентификатор'), primary_key=True, default=uuid4, editable=False)
    firstname = models.CharField(_('имя'), max_length=128)
    lastname = models.CharField(_('фамилия'), max_length=128)
    birthdate = models.DateField(_('дата рождения'))
    birthplace = models.CharField(_('место рождения'), max_length=255)

    class Meta:
        verbose_name = _('Человек')
        verbose_name_plural = _('Люди')
        constraints = [
            models.UniqueConstraint(fields=['firstname', 'lastname', 'birthdate', 'birthplace'], name='person_unique')
        ]
        db_table = f'"{os.getenv("MOVIES_SCHEMA", "content")}"."movies_person"'

    def __str__(self):
        return f'{self.firstname} {self.lastname}'

    def clean(self):
        """Подстраховка на добавление одиннаковых людей."""
        self.firstname = self.firstname.capitalize()
        self.lastname = self.lastname.capitalize()
        self.birthplace = self.birthplace.capitalize()
        super().clean()


class RoleType(models.TextChoices):
    """Роли/профессии людей в кинопроизведениях."""
    director = 'director', _('режиссер')
    actor = 'actor', _('актер')
    writer = 'writer', _('сценарист')


class MoviePerson(TimeStampedModel):
    """Промежуточная таблица кинопроизведений и людей."""
    id = models.UUIDField(_('идентификатор'), primary_key=True, default=uuid4, editable=False)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, verbose_name=_('кинопроизведение'))
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name=_('человек'))
    role = models.CharField(_('роль'), max_length=20, choices=RoleType.choices, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['movie', 'person', 'role'], name='movie_person_unique')
        ]
        db_table = f'"{os.getenv("MOVIES_SCHEMA", "content")}"."movies_movieperson"'

    def __str__(self):
        return f'{self.movie} - {self.person} - {self.get_role_display()}'
