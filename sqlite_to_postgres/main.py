import sqlite3

import psycopg2
from extract_data_from_sqlite import SQLiteLoader
from load_data_to_postgres import PostgresSaver
from psycopg2.extensions import connection as _connection
from settings import dsn


def load_data_from_sqlite_to_postgres(
    connection: sqlite3.Connection, pg_conn: _connection
):
    """Основной метод загрузки данных из SQLite в Postgres."""
    sqlite_loader = SQLiteLoader(connection)
    postgres_saver = PostgresSaver(pg_conn)

    data = sqlite_loader.load_movies()
    postgres_saver.save_all_data(data)


if __name__ == "__main__":
    with sqlite3.connect("db.sqlite") as sqlite_conn, psycopg2.connect(
        **dsn
    ) as postgres_conn:
        load_data_from_sqlite_to_postgres(sqlite_conn, postgres_conn)
