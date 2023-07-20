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


def get_url_by_id(id):
    with connect(DATABASE_URL) as cursor:
        cursor.execute("SELECT * FROM urls WHERE id = '{}'".format(id))
        return cursor.fetchone()


def get_url_checks_by_id(id):
    with connect(DATABASE_URL) as cursor:
        cursor.execute("SELECT * FROM url_checks WHERE url_id = '{}'".format(id))
        return cursor.fetchall()


def get_url_id_by_name(name):
    with connect(DATABASE_URL) as cursor:
        cursor.execute("SELECT id FROM urls WHERE name = '{}'".format(name))
        return cursor.fetchone()


def get_sites():
    with connect(DATABASE_URL) as cursor:
        cursor.execute("""
                    SELECT DISTINCT urls.id, urls.name, urls.created_at, url_checks.created_at, url_checks.status_code
                    FROM urls
                    LEFT JOIN (
                        SELECT url_id, MAX(created_at) AS max_created_at
                        FROM url_checks
                        GROUP BY url_id
                    ) latest_checks ON latest_checks.url_id = urls.id
                    LEFT JOIN url_checks ON url_checks.url_id = urls.id AND url_checks.created_at = latest_checks.max_created_at
                    ORDER BY urls.id
                    """)
        return cursor.fetchall()


def create_url(name, creation_date):
    with connect(DATABASE_URL, True) as cursor:
        cursor.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id;", (name, creation_date))
        return cursor.fetchone()[0]


def create_check(id, code, h1, title, description, date1):
    with connect(DATABASE_URL, True) as cursor:
        cursor.execute('''INSERT INTO url_checks
                    (url_id, status_code, h1, title, description, created_at)
                    VALUES ('{}', '{}', '{}', '{}', '{}', '{}')
                    ;'''.format(id, code, h1, title, description, date1))
        cursor.execute("SELECT * FROM url_checks WHERE url_id = '{}'".format(id))
        return cursor.fetchall()
