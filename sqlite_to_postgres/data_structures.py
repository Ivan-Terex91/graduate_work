import hashlib
import logging
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger("data_structures_logger")


def hash_maker(primary_key: str) -> str:
    return str(hashlib.sha3_256(primary_key.encode()).hexdigest())


@dataclass
class Person:
    name: str
    id: str


@dataclass
class FilmWork:
    title: str
    description: Optional[str]
    rating: Optional[float]
    id: str


@dataclass
class PersonFilm:
    film_work_id: str
    person_id: str
    role: str
    id: str


@dataclass
class Genre:
    name: str
    id: str


@dataclass
class GenreFilm:
    film_work_id: str
    genre_id: str
    id: str


@dataclass
class DatabaseMovies:
    person_table: Dict[str, Person] = field(default_factory=dict)
    film_work_table: List[FilmWork] = field(default_factory=list)
    genre_table: Dict[str, Genre] = field(default_factory=dict)
    genre_film_work_table: List[GenreFilm] = field(default_factory=list)
    person_film_work_table: List[PersonFilm] = field(default_factory=list)

    def parse_row(self, row: Dict[str, Any]):
        """Parse row from sqlite and add data to all tables"""
        try:
            film_work_id = self.add_film(row)
            self.add_persons(row["writers"], film_work_id, "writer")
            self.add_persons(row["actors"], film_work_id, "actor")
            self.add_persons(row["director"], film_work_id, "director")

            self.add_genres(row["genre"], film_work_id)

        except KeyError as e:
            log.error('Parsing row does not have field "%s"', e.args[0])
            raise ValueError(
                "Parsed data doesn't have all required arguments"
            ).with_traceback(sys.exc_info()[2])

    def add_film(self, row: Dict[str, Any]) -> str:
        """
        Parse row from sqlite and add movie to film_work
        :return: return uuid of created film_work row
        """
        film_work = FilmWork(
            id=hash_maker(row["id"]),
            title=row["title"],
            description=row["plot"],
            rating=row["imdb_rating"],
        )

        self.film_work_table.append(film_work)
        log.debug(
            'Film title="%s", id="%s" added to film_work_table with new id="%s"',
            row["title"],
            row["id"],
            film_work.id,
        )
        return film_work.id

    def add_persons(
        self, persons: List[Dict[str, str]], film_work_id: str, role: str
    ) -> None:
        """
        Parse list of persons and add all unique and new persons to person_table.
        Also add relationship between person and film to person_film_work_table
        """
        for person in persons:
            person_id, person_name = person.values()

            existing_person = self.person_table.get(hash_maker(person_name))
            if not existing_person:
                existing_person = Person(id=hash_maker(person_name), name=person_name,)
                self.person_table[person_id] = existing_person
                log.debug(
                    'Person name="%s", id="%s" was added to person_table with new id="%s"',
                    person_name,
                    person_id,
                    existing_person.id,
                )
            else:
                log.debug(
                    'Person name="%s", id="%s" has already been added to person_table',
                    person_name,
                    person_id,
                )

            self.add_person_film_relation(existing_person.id, film_work_id, role)

    def add_person_film_relation(self, person_id: str, film_id: str, role: str) -> None:
        """
        Add relationship between person and film to person_film_work_table
        """
        self.person_film_work_table.append(
            PersonFilm(
                id=hash_maker(str(film_id) + str(person_id) + role),
                film_work_id=film_id,
                person_id=person_id,
                role=role,
            )
        )
        log.debug(
            'Relationship of person "%s" and film "%s" with role "%s" was added to person_film_work_table',
            person_id,
            film_id,
            role,
        )

    def add_genres(self, genres: List[str], film_work_id: str) -> None:
        """
        Parse list of genres and add all new genres to genre_table.
        """
        for genre in genres:
            existing_genre = self.genre_table.get(genre)

            if not existing_genre:
                existing_genre = Genre(id=hash_maker(genre), name=genre)
                self.genre_table[genre] = existing_genre
                log.debug(
                    'Genre name="%s" was added to genre_table with new id="%s"',
                    genre,
                    existing_genre.id,
                )
            else:
                log.debug(
                    'Genre name="%s", id="%s" has already been added to genre_table',
                    existing_genre.name,
                    existing_genre.id,
                )

            self.add_genre_film_relation(existing_genre.id, film_work_id)

    def add_genre_film_relation(self, genre_id: str, film_id: str) -> None:
        """
        Add relationship between genre and film to genre_film_work_table
        """
        self.genre_film_work_table.append(
            GenreFilm(
                id=hash_maker(str(film_id) + str(genre_id)),
                film_work_id=film_id,
                genre_id=genre_id,
            )
        )
        log.debug(
            'Relationship of genre "%s" and film "%s" was added to genre_film_work_table',
            genre_id,
            film_id,
        )
