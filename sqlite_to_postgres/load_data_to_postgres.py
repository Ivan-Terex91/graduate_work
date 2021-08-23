from random import randrange

import psycopg2.extras
from my_dataclasses import (Genre, Movie, MovieGenre, MoviePerson, Person,
                            random_date)

psycopg2.extras.register_uuid()


class PostgresSaver:
    """Класс загрузки данных в Postgres."""

    def __init__(self, connection):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.movies_from_sqlite = []

    def load_movie(self, single_movie: dict) -> str:
        """Загрузка фильма."""

        movie = Movie(
            title=single_movie.get("title"),
            description=single_movie.get("description"),
            imdb_rating=single_movie.get("imdb_rating") or randrange(0, 10),
            creation_date=random_date(),
        )
        data = (
            movie.id,
            movie.title,
            movie.movie_type,
            movie.file_path,
            movie.description,
            movie.imdb_rating,
            movie.rating,
            movie.creation_date,
            movie.age_limit,
            movie.created,
            movie.modified,
        )

        self.cursor.execute(
            f"""
                 INSERT INTO content.movies_movie(id, title, movie_type, file_path, description, imdb_rating, rating, 
                 creation_date, age_limit, created, modified )
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                 ON CONFLICT ON CONSTRAINT movie_unique DO NOTHING
                 RETURNING content.movies_movie.id;
                 """,
            data,
        )
        movie_returning_id = self.cursor.fetchone()
        movie_id = movie_returning_id[0] if movie_returning_id else movie.id
        return movie_id

    def load_genre_and_movie_genre(self, single_movie, movie_id):
        """Загрузка жанра и заполнение таблицы movie_genre."""

        genres = single_movie.get("genre")
        for genre in genres:
            _genre = Genre(name=genre)
            data = (
                _genre.id,
                _genre.name,
                _genre.description,
                _genre.created,
                _genre.modified,
            )
            self.cursor.execute(
                f"""
                WITH query_sel AS (
                    SELECT content.movies_genre.id FROM content.movies_genre
                    WHERE content.movies_genre.name = %s
                ), query_ins AS (
                    INSERT INTO content.movies_genre(id, name, description, created, modified)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO NOTHING
                    RETURNING id
                )

                SELECT %s as id FROM query_ins
                UNION ALL
                SELECT id AS id from query_sel;
            """,
                (_genre.name, *data, _genre.id),
            )
            genre_id = self.cursor.fetchone()[0]

            movie_genre = MovieGenre(movie_id=movie_id, genre_id=genre_id)
            data = (movie_genre.movie_id, movie_genre.genre_id)
            self.cursor.execute(
                f"""
                                INSERT INTO content.movies_movie_genres(movie_id, genre_id)
                                VALUES (%s, %s)
                                ON CONFLICT ON CONSTRAINT movies_movie_genres_movie_id_genre_id_5ff3c723_uniq DO NOTHING
                """,
                data,
            )

    def load_person_and_movie_person(self, single_movie: dict, movie_id):
        """Загрузка людей и заполнение таблицы movie_person."""

        person_list = single_movie.get("persons")
        for person in person_list:
            _person = Person(firstname=person[0], role=person[1])
            if not _person.firstname:
                continue
            data = (
                _person.id,
                _person.firstname,
                _person.lastname,
                _person.birthdate,
                _person.birthplace,
                _person.created,
                _person.modified,
            )
            self.cursor.execute(
                f"""
                WITH query_sel AS (
                    SELECT content.movies_person.id FROM content.movies_person
                    WHERE content.movies_person.firstname = %s
                    ), query_ins AS (
                    INSERT INTO content.movies_person(id, firstname, lastname, birthdate, birthplace, created, modified)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT ON CONSTRAINT person_unique DO NOTHING
                    RETURNING id
                )

                SELECT %s as id FROM query_ins
                UNION ALL
                SELECT id AS id from query_sel;
                """,
                (_person.firstname, *data, _person.id),
            )
            person_id = self.cursor.fetchone()[0]

            movie_person = MoviePerson(
                movie_id=movie_id, person_id=person_id, role=_person.role
            )
            data = (
                movie_person.id,
                movie_person.movie_id,
                movie_person.person_id,
                movie_person.role,
                movie_person.created,
                movie_person.modified,
            )
            self.cursor.execute(
                f"""
                               INSERT INTO content.movies_movieperson(id, movie_id, person_id, role, created, modified)
                               VALUES (%s, %s, %s, %s, %s, %s)
                               ON CONFLICT ON CONSTRAINT movie_person_unique DO NOTHING
               """,
                data,
            )

    def save_all_data(self, movies_from_sqlite):
        """Загрузка всех фильмов."""
        self.movies_from_sqlite = movies_from_sqlite

        for movie in self.movies_from_sqlite:
            movie_id = self.load_movie(movie)
            self.load_genre_and_movie_genre(movie, movie_id)
            self.load_person_and_movie_person(movie, movie_id)
