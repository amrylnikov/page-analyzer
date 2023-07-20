import os
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


@contextmanager
def connect(bd_url, autocommit_flag=False):
    try:
        connection = psycopg2.connect(bd_url)
        if autocommit_flag:
            connection.autocommit = True
        cursor = connection.cursor()
        yield cursor
    finally:
        cursor.close()
        connection.close()


def get_url_by_id(id, flag=False):
    with connect(DATABASE_URL, flag) as cursor:
        cursor.execute("SELECT * FROM urls WHERE id = '{}'".format(id))
        return cursor.fetchone()


def get_url_checks_by_id(id, flag=False):
    with connect(DATABASE_URL, flag) as cursor:
        cursor.execute("SELECT * FROM url_checks WHERE url_id = '{}'".format(id))
        return cursor.fetchall()


def create_url(name):
    pass
