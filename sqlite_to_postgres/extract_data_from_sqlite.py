import json


class SQLiteLoader:
    """Класс загрузки фильмов из sqlite."""

    def __init__(self, connection):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.all_movie_list = []
        self.transform_movie_list = []

    def load_movies(self) -> list:
        """Метод загрузки всех фильмов."""
        sql_command_for_all_movies = """
                     SELECT m.id, m.imdb_rating, m.genre, m.title, 
                     m.plot, m.director, m.writer, m.writers
                     FROM movies AS m"""

        for row in self.cursor.execute(sql_command_for_all_movies):
            self.all_movie_list.append(row)

        for _movie in self.all_movie_list:
            movie = Movie(self.cursor, *_movie)
            movie.transform_data()
            self.transform_movie_list.append(movie.__dict__)

        return self.transform_movie_list


class Movie:
    """Фильмы."""

    def __init__(
        self,
        cursor,
        idx,
        imdb_rating,
        genre,
        title,
        description,
        director,
        writer,
        writers,
    ):
        self.cursor = cursor
        self.id = idx
        self.imdb_rating = float(imdb_rating) if imdb_rating != "N/A" else None
        self.genre = genre.replace(" ", "").split(",")
        self.title = title
        self.description = description if description != "N/A" else None
        self.directors = director.split(", ") if director != "N/A" else None
        self.actors_names = set()
        self.writers_names = set()
        self.actors = []
        self.writer = writer
        self.writers = json.loads(writers) if writers else None
        self.persons = []

    def actor_list(self):
        """Формирует список словарей актёров {"id": int, "name": str}."""
        sql_actors = f""" 
                          SELECT actor_id, actors.name
                          FROM movie_actors INNER JOIN actors ON
                          movie_actors.actor_id = actors.id
                          WHERE movie_id = '{self.id}'
                      """

        for row in self.cursor.execute(sql_actors):
            if row[1] == "N/A":
                continue
            self.actors.append({"id": int(row[0]), "name": row[1]})
            self.actors_names.add(row[1])
        self.actors_names = list(self.actors_names)

    def writer_list(self):
        """Формирует список словарей сценаристов {"id": str, "name": str}."""
        if self.writers:
            writers = self.writers
            writers_list = [list(writer.values()) for writer in writers]
            writers_list = [
                writer for writer_sub_list in writers_list for writer in writer_sub_list
            ]
            writers_list = list(set(writers_list))
        else:
            writers_list = [self.writer]
        self.writers = []

        for writer in writers_list:
            self.cursor.execute(
                f"""SELECT writers.id, writers.name
                               FROM writers
                               WHERE writers.id = '{writer}'"""
            )
            writer_data = self.cursor.fetchall()[0]
            if writer_data[1] == "N/A":
                continue
            self.writers.append({"id": writer_data[0], "name": writer_data[1]})
            self.writers_names.add(writer_data[1])
        self.writers_names = list(self.writers_names)

    def person_list(self):
        """Формируем список людей и их ролями(профессиями)."""
        directors = (
            [(director, "director") for director in self.directors]
            if self.directors
            else [(None, "director")]
        )
        self.persons.extend(directors)
        actors = (
            [(actor.get("name"), "actor") for actor in self.actors]
            if self.actors
            else [(None, "actor")]
        )
        self.persons.extend(actors)
        writers = (
            [(writer.get("name"), "writer") for writer in self.writers]
            if self.writers
            else [(None, "writer")]
        )
        self.persons.extend(writers)

    def transform_data(self):
        """Метод нормализации данных."""
        self.actor_list()
        self.writer_list()
        self.person_list()
        del self.cursor, self.writer


if __name__ == "__main__":
    import sqlite3

    with sqlite3.connect("db.sqlite") as sqlite_conn:
        sqlite_loader = SQLiteLoader(sqlite_conn)
        data = sqlite_loader.load_movies()
