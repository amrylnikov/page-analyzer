from datetime import date

from psycopg2 import extras


def get_url_by_id(conn, id):
    with conn.cursor(cursor_factory=extras.NamedTupleCursor) as cursor:
        cursor.execute("""
                    SELECT id, name, created_at
                    FROM urls
                    WHERE id = %s;
                    """, (id,))
        return cursor.fetchone()


def get_url_checks_by_id(conn, id):
    with conn.cursor() as cursor:
        cursor.execute("""
                    SELECT id, url_id, status_code, h1, title, description,
                       created_at
                    FROM url_checks
                    WHERE url_id = %s;
                    """, (id,))
        return cursor.fetchall()


def get_url_by_name(conn, name):
    with conn.cursor() as cursor:
        cursor.execute("""
                    SELECT id, name, created_at
                    FROM urls
                    WHERE name = %s;
                    """, (name,))
        return cursor.fetchone()


def get_all_url_checks(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
                    SELECT DISTINCT ON (urls.id) urls.id, urls.name,
                       url_checks.created_at, url_checks.status_code
                    FROM urls
                    LEFT JOIN url_checks ON url_checks.url_id = urls.id
                    ORDER BY urls.id
                    LIMIT 100 OFFSET 0;
                    """)
        return cursor.fetchall()


def create_url(conn, name):
    creation_date = date.today()
    with conn.cursor() as cursor:
        cursor.execute("""
                    INSERT INTO urls (name, created_at)
                    VALUES (%s, %s)
                    RETURNING id;
                    """, (name, creation_date))
        return cursor.fetchone()[0]


def create_check(conn, id, code, h1, title, description):
    with conn.cursor() as cursor:
        creation_date = date.today()
        cursor.execute("""
                    INSERT INTO url_checks
                    (url_id, status_code, h1, title, description, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """, (id, code, h1, title, description, creation_date))


def get_check_by_url_id(conn, id):
    with conn.cursor() as cursor:
        cursor.execute("""
                    SELECT id, url_id, status_code, h1, title, description,
                       created_at
                    FROM url_checks
                    WHERE url_id = %s;
                    """, (id,))
        return cursor.fetchall()
