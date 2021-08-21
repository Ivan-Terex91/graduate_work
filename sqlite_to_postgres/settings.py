from dataclasses import dataclass
from typing import Dict

from environs import Env


@dataclass
class Settings:
    dbname: str
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    sqlite_file: str
    batch_size: int

    def __init__(self, file_name: str):
        self.env = Env()
        self.env.read_env(file_name)

        self.dbname = self.env('dbname')
        self.db_user = self.env('db_user')
        self.db_password = self.env('db_password')
        self.db_host = self.env('db_host')
        self.db_port = self.env('db_port')
        self.sqlite_file = self.env('sqlite_file')
        self.batch_size = int(self.env('batch_size'))

    def get_pg_settings(self) -> Dict[str, str]:
        return {
            'dbname': self.dbname,
            'user': self.db_user,
            'password': self.db_password,
            'host': self.db_host,
            'port': self.db_port,
        }
