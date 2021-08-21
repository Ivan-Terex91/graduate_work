import json
import logging
import sqlite3
import sys
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union

import psycopg2
from psycopg2.extensions import connection as pg_connection
from psycopg2.extras import DictCursor, execute_batch

from data_structures import DatabaseMovies
from settings import Settings

logging.basicConfig(
    format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
    level=logging.INFO,
)
log = logging.getLogger('load_data_logger')


def load_from_sqlite(
    connection: sqlite3.Connection, pg_conn: pg_connection, batch_size: int
):
    '''Основной метод загрузки данных из SQLite в Postgres'''
    log.debug('Start ETL process')
    postgres_saver = PostgresSaver(pg_conn, batch_size)
    sqlite_loader = SQLiteLoader(connection)

    log.debug('Start loading data from sqlite')
    data = sqlite_loader.load_movies()

    log.debug('Start loading data to comparing')
    postgres_saver.save_all_data(data, batch_size)


class HasConnection:
    @abstractmethod
    def __init__(self, db_connection: Union[pg_connection, sqlite3.Connection]):
        self._connection = db_connection


class PostgresSaver(HasConnection):
    FILM_WORK_INSERT = '''
    INSERT INTO content.film_work
    (id, title, description, rating, type, created_at, updated_at)
    VALUES
    (%s, %s, %s, %s, 'movie', clock_timestamp(), clock_timestamp())
    ON CONFLICT (id) DO NOTHING
    '''

    PERSON_INSERT = '''
    INSERT INTO content.person
    (id, name, created_at, updated_at)
    VALUES
    (%s, %s, clock_timestamp(), clock_timestamp())
    ON CONFLICT (id) DO NOTHING
    '''

    GENRE_INSERT = '''
    INSERT INTO content.genre
    (id, name, created_at, updated_at)
    VALUES
    (%s, %s, clock_timestamp(), clock_timestamp())
    ON CONFLICT (id) DO NOTHING
    '''

    PERSON_FILM_WORK_INSERT = '''
    INSERT INTO content.person_film_work
    (id, film_work_id, person_id, role, created_at)
    VALUES
    (%s, %s, %s, %s, clock_timestamp())
    ON CONFLICT (id) DO NOTHING
    '''

    GENRE_FILM_WORK_INSERT = '''
    INSERT INTO content.genre_film_work
    (id, film_work_id, genre_id, created_at)
    VALUES
    (%s, %s, %s, clock_timestamp())
    ON CONFLICT (id) DO NOTHING
    '''

    def __init__(self, db_connection: pg_connection, batch_size: int):
        super().__init__(db_connection)

    def save_all_data(self, data: List[Dict[str, Any]], batch_size: int) -> None:
        '''
        Get data from slqlite, transform it and load to comparing
        '''
        tables = DatabaseMovies()
        for row in data:
            tables.parse_row(row)

        self._upload_data_to_database(tables, batch_size)
        self._connection.commit()
        log.info('all data uploaded to databased and saved')

    def _upload_data_to_database(self, tables: DatabaseMovies, batch_size: int) -> None:
        '''
        Upload all data to comparing database
        '''
        self._connection.autocommit = False
        insert_cursor = self._connection.cursor()

        execute_batch(
            insert_cursor,
            self.FILM_WORK_INSERT,
            [
                (film.id, film.title, film.description, film.rating)
                for film in tables.film_work_table
            ],
            page_size=batch_size,
        )
        log.info('film_works table was loaded to database')

        execute_batch(
            insert_cursor,
            self.PERSON_INSERT,
            [(person.id, person.name) for person in tables.person_table.values()],
            page_size=batch_size,
        )
        log.info('person_table table was loaded to database')

        execute_batch(
            insert_cursor,
            self.GENRE_INSERT,
            [(genre.id, genre.name) for genre in tables.genre_table.values()],
            page_size=batch_size,
        )
        log.info('genre_table table was loaded to database')

        execute_batch(
            insert_cursor,
            self.PERSON_FILM_WORK_INSERT,
            [
                (record.id, record.film_work_id, record.person_id, record.role)
                for record in tables.person_film_work_table
            ],
            page_size=batch_size,
        )
        log.info('person_film_table table was loaded to database')

        execute_batch(
            insert_cursor,
            self.GENRE_FILM_WORK_INSERT,
            [
                (record.id, record.film_work_id, record.genre_id)
                for record in tables.genre_film_work_table
            ],
            page_size=batch_size,
        )
        log.info('genre_film_work_table table was loaded to database')


class SQLiteLoader(HasConnection):
    SQL = """
    WITH x as (
    SELECT m.id, '['|| group_concat('{"id": "' || a.id ||  '", "name": "' || a.name || '"}') || ']' as actors
    FROM movies m
    LEFT JOIN movie_actors ma on m.id = ma.movie_id
    LEFT JOIN actors a on ma.actor_id = a.id
    GROUP BY m.id
    )
    SELECT m.id, title, plot, genre, director, imdb_rating, x.actors,
    CASE
        WHEN m.writers = '' THEN '[{"id": "' || m.writer || '"}]'
        ELSE m.writers
    END as writers
    from movies as m
    LEFT OUTER JOIN x on m.id = x.id;
    """

    def __init__(self, db_connection: sqlite3.Connection):
        super().__init__(db_connection)

    def load_movies(self) -> List[Dict[str, Any]]:
        '''
        Get data from sqlite and transform it in suitable form
        :return: return all data from sqlite in one table
        '''
        try:
            writers_dict = self._load_writers()
            records = []
            for row in self._connection.execute(self.SQL):
                log.debug('loaded row "%s"', row)
                transformed_row = self._transform_row(row, writers_dict)
                records.append(transformed_row)

        except KeyError as e:
            log.error('Loaded row does not have field "%s"', e.args[0])
            raise ValueError(
                "Loaded data doesn't have all required arguments"
            ).with_traceback(sys.exc_info()[2])

        return records

    def _load_writers(self) -> Dict[str, str]:
        '''
        Load full table of writers from sqlite in form of dict
        :return: mapping of all writers' names by their id
        '''
        select_cursor = self._connection.execute('SELECT * FROM writers')
        writers_table = {}
        for writer in select_cursor.fetchall():
            writers_table[writer['id']] = writer['name']

        log.debug(
            'Writers table loaded to memory: %s rows were loaded', len(writers_table)
        )
        return writers_table

    def _transform_row(
        self, row: Dict[str, Any], writers_table: Dict[str, str]
    ) -> Dict[str, Any]:
        '''
        Validating fields and transform to suitable form
        :return: validated row
        '''
        row['writers'] = self._transform_writers(row['writers'], writers_table)
        row['actors'] = self._transform_actors(row['actors'])

        if self._na_checking(row['imdb_rating'], 'imdb_rating'):
            row['imdb_rating'] = float(row['imdb_rating'])
        else:
            row['imdb_rating'] = None

        row['plot'] = self._na_checking(row['plot'], 'plot')
        row['genre'] = [genre_name.strip() for genre_name in row['genre'].split(',')]

        directors = row['director']
        if directors:
            directors = directors.split(', ')
            # we don't have directors id, so we can use their full name as id
            parsed_directors = []
            for person in directors:
                parsed_directors.append({'id': person, 'name': person})
            row['director'] = self._transform_persons(parsed_directors)

        return row

    @classmethod
    def _transform_writers(
        cls, row_writers: str, writers_table: Dict[str, str]
    ) -> List[Dict[str, str]]:
        '''
        Getting movie writers names and validate
        :return: validated writers list
        '''
        writers_id = [writer['id'] for writer in json.loads(row_writers)]
        log.debug('parsed writers ids="%s"', writers_id)
        film_writers = cls._get_writers_names(writers_id, writers_table)
        return cls._transform_persons(film_writers)

    @staticmethod
    def _get_writers_names(
        writers_ids: List[str], writers_table: Dict[str, str]
    ) -> List[Dict[str, str]]:
        '''
        Getting movie writers names from writers' table
        :return: list of writers with their names
        '''
        film_writers = []

        for writer_id in writers_ids:
            film_writers.append({'id': writer_id, 'name': writers_table[writer_id]})
            log.debug(
                'for writer id="%s" found name in writers table name="%s"',
                writer_id,
                writers_table[writer_id],
            )

        return film_writers

    @classmethod
    def _transform_actors(cls, row_actors: str) -> List[Dict[str, str]]:
        '''
        Load actors from json and validate
        :return: validated actors list
        '''
        film_actors = json.loads(row_actors)
        log.debug('loaded film actors "%s"', film_actors)
        return cls._transform_persons(film_actors)

    @classmethod
    def _transform_persons(cls, persons: List[Dict[str, str]]) -> List[dict]:
        '''
        Validate person's list and transform to suitable form
        :return: validated list of persons
        '''
        transformed_persons = {}

        for person in persons:
            person_id, person_name = person.values()
            if cls._na_checking(person_name, 'person_name'):
                log.debug('Person name="%s"', person_name)

                transformed_persons[person_id] = {
                    'id': person_id,
                    'name': person_name,
                }
            else:
                log.debug('missing person id="%s" with empty name', person_id)

        return list(transformed_persons.values())

    @staticmethod
    def _na_checking(argument: str, argument_name: str = None) -> Optional[str]:
        '''
        Check argument is 'N/A' or not
        '''
        if argument == 'N/A':
            log.debug(
                'Argument "%s" had "N/A" value and was replaced with "None"',
                argument_name,
            )
            return None
        return argument


def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    '''
    Так как в SQLite нет встроенной фабрики для строк в виде dict,
    всё приходится делать самостоятельно
    '''
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def create_schema(db_conn: pg_connection, path_schema_file: str):
    log.info('Creating database schema')
    with db_conn.cursor() as cursor:
        with open(path_schema_file, mode='r') as file_db_schema:
            sql_schema = file_db_schema.read()
            log.debug(sql_schema)

            try:
                cursor.execute(sql_schema)
            except Exception as e:
                log.error("Database schema can't be created!")
                log.error(e)

            db_conn.commit()


if __name__ == '__main__':
    settings = Settings('.env')
    log.info("Database's parameters are: %s", settings.get_pg_settings())

    with sqlite3.connect(settings.sqlite_file) as sqlite_conn, psycopg2.connect(
        **settings.get_pg_settings(), cursor_factory=DictCursor
    ) as pg_conn:
        create_schema(pg_conn, 'autor_database_schema.sql')
        sqlite_conn.row_factory = dict_factory
        load_from_sqlite(sqlite_conn, pg_conn, settings.batch_size)
