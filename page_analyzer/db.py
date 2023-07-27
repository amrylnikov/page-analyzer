import os
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


# Переделать по ссылке из тг, поизучать, и курсор там отдельно как-то... Отдельно в каждой функции по ссылке, которую Андрей кинул L31
@contextmanager
def get_cursor(connection):
    try:
        cursor = connection.cursor()
        yield cursor
    finally:
        cursor.close()


# не закрывать коннект сразу, ибо каждый раз подключиться - затратно
# Открывать и закрывать коннекшн в рамках функции в app, а не для каждого запроса
def get_url_by_id(conn, id):
    with get_cursor(conn) as cursor:
        cursor.execute("SELECT * FROM urls WHERE id = %s", (id,))
        return cursor.fetchone()


# И вместо звёздочек в запросе SELECT * FROM url_checks WHERE перечисляй всё, ибо для стороннего непонятно.
# И в курсоре передавать переменные
def get_url_checks_by_id(conn, id):
    with get_cursor(conn) as cursor:
        cursor.execute("SELECT * FROM url_checks WHERE url_id = %s", (id,))
        return cursor.fetchall()


def get_url_id_by_name(conn, name):
    with get_cursor(conn) as cursor:
        cursor.execute("SELECT id FROM urls WHERE name = %s", (name,))
        return cursor.fetchone()


# название смени get_all_url_checks
def get_sites(conn):
    with get_cursor(conn) as cursor:
        # urls.created_at не надо
        # Попытаться упростить, DISTINCT на одно поле сделать "dittinct by one column"
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


# И creation_date создавать прям в этой функции, а не передавать, чтоб функция была самодостаточной.
def create_url(conn, name, creation_date):
    with get_cursor(conn) as cursor:
        cursor.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id;", (name, creation_date))
        return cursor.fetchone()[0]


# date1 замени на creation_date ибо одно и то же
def create_check(conn, id, code, h1, title, description, date1):
    with get_cursor(conn) as cursor:
        cursor.execute('''INSERT INTO url_checks
                    (url_id, status_code, h1, title, description, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ;''', (id, code, h1, title, description, date1))
        cursor.execute("SELECT * FROM url_checks WHERE url_id = %s", (id,))
        return cursor.fetchall()
