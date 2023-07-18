import os
from datetime import date
from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg2
import requests
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    get_flashed_messages,
    render_template,
    request,
    redirect,
    url_for
)

from page_analyzer.validator import validate
from page_analyzer.functions import parse

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
app = Flask(__name__)
app.secret_key = SECRET_KEY


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


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def urls_display():
    with connect(DATABASE_URL) as cursor:
        cursor.execute("""
                    SELECT DISTINCT urls.id, urls.name, urls.created_at, url_checks.created_at, url_checks.status_code
                    FROM urls
                    LEFT JOIN url_checks ON url_checks.url_id = urls.id
                    """)
        urls = cursor.fetchall()
    return render_template(
        '/urls.html',
        urls=urls
    )


@app.post('/urls')
def urls_add():
    url_name = request.form.get('url')
    errors = validate(url_name)
    if errors:
        return render_template(
            'index.html',
            errors=errors,
        ), 422
    url_parsed = urlparse(url_name)
    url_name = url_parsed.scheme + '://' + url_parsed.netloc
    creation_date = date.today()
    with connect(DATABASE_URL, True) as cursor:
        cursor.execute("SELECT id FROM urls WHERE name = '{}'".format(url_name))
        id = cursor.fetchone()
        if id:
            flash('Страница уже существует', 'info')
            return redirect(url_for('url_info', id=id[0]))
        cursor.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id;", (url_name, creation_date))
        id = cursor.fetchone()[0]
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('url_info', id=id))


@app.route('/urls/<id>')
def url_info(id):
    with connect(DATABASE_URL) as cursor:
        cursor.execute("SELECT * FROM urls WHERE id = '{}'".format(id))
        temp = cursor.fetchone()
        cursor.execute("SELECT * FROM url_checks WHERE url_id = '{}'".format(id))
        checks = cursor.fetchall()
    name = temp[1]
    created_at = temp[2]
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'urls_id.html',
        id=id,
        name=name,
        created_at=created_at,
        checks=checks,
        messages=messages
    )


@app.route('/urls/<id>/checks', methods=['GET', 'POST'])
def url_check(id):
    with connect(DATABASE_URL, True) as cursor:
        cursor.execute("SELECT name FROM urls WHERE id = '{}'".format(id))
        cursor.execute("SELECT * FROM urls WHERE id = '{}'".format(id))
        temp = cursor.fetchone()
        name = temp[1]
        created_at = temp[2]
        try:
            r = requests.get(name)
        except Exception:
            flash('Произошла ошибка при проверке', 'error')
            messages = get_flashed_messages(with_categories=True)
            return render_template(
                'urls_id.html',
                id=id,
                name=name,
                created_at=created_at,
                messages=messages,
                checks=[]
            )
        code, h1, title, description = parse(r)
        date1 = date.today()
        cursor.execute('''INSERT INTO url_checks
                    (url_id, status_code, h1, title, description, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ;''', (id, code, h1, title, description, date1))
        cursor.execute("SELECT * FROM url_checks WHERE url_id = '{}'".format(id))
        checks = cursor.fetchall()

    flash('Страница успешно проверена', 'success')
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'urls_id.html',
        id=id,
        name=name,
        created_at=created_at,
        messages=messages,
        checks=checks
    )
