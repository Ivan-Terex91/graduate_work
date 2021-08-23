"""Этот модуль содержит изменённые датаклассы по сравнению с прошлым спринтом, т.к.
в базе sqlite3 не предусмотренны поля которые есть в базе postgres"""

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from random import randrange


def random_date():
    """Функция для генерации дат"""
    start = date.today()
    return start - timedelta(days=randrange(1, 36500))


class RoleType(Enum):
    """Роли в фильме"""

    actor = "actor"
    writer = "writer"
    director = "director"


@dataclass
class Movie:
    """Фильмы"""

    title: str
    creation_date: str
    description: str = field(default="description")
    movie_type: str = field(default="movie")
    file_path: str = field(default="")
    imdb_rating: float = field(default=0.0)
    rating: float = field(default=0.0)
    age_limit: int = field(default=0)
    created: str = field(default=datetime.now())
    modified: str = field(default=datetime.now())
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class Genre:
    """Жанры."""

    name: str
    description: str = field(default="description")
    created: str = field(default=datetime.now())
    modified: str = field(default=datetime.now())
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class Person:
    """Люди."""

    firstname: str
    role: str
    lastname: str = field(default="")
    birthdate: str = field(default=random_date())
    birthplace: str = field(default="Saint-Petersburg")
    created: str = field(default=datetime.now())
    modified: str = field(default=datetime.now())
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class MovieGenre:
    """Связь фильмов и жанров."""

    movie_id: uuid.UUID = field(default_factory=uuid.uuid4)
    genre_id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class MoviePerson:
    """Связь фильмов и людей"""

    role: RoleType
    movie_id: uuid.UUID = field(default_factory=uuid.uuid4)
    person_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created: str = field(default=datetime.now())
    modified: str = field(default=datetime.now())
    id: uuid.UUID = field(default_factory=uuid.uuid4)
