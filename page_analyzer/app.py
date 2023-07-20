import os
from contextlib import contextmanager
from datetime import date
from urllib.parse import urlparse

import psycopg2
import requests
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for

from page_analyzer.functions import parse
from page_analyzer.validator import validate
from page_analyzer import db

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def urls_display():
    urls = db.get_sites()
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
    id = db.get_url_id_by_name(url_name)
    if id:
        flash('Страница уже существует', 'info')
        return redirect(url_for('url_info', id=id[0]))
    id = db.create_url(url_name, creation_date)
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('url_info', id=id))


@app.route('/urls/<id>')
def url_info(id):
    url = db.get_url_by_id(id)
    if not url:
        abort(404)
    name = url[1]
    created_at = url[2]
    checks = db.get_url_checks_by_id(id)
    return render_template(
        'urls_id.html',
        id=id,
        name=name,
        created_at=created_at,
        checks=checks
    )


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


@app.route('/urls/<id>/checks', methods=['GET', 'POST'])
def url_check(id):
    url = db.get_url_by_id(id)
    if not url:
        abort(404)
    name = url[1]
    created_at = url[2]
    with connect(DATABASE_URL, True) as cursor:
        try:
            r = requests.get(name)

            code, h1, title, description = parse(r)
            date1 = date.today()
            cursor.execute('''INSERT INTO url_checks
                        (url_id, status_code, h1, title, description, created_at)
                        VALUES ('{}', '{}', '{}', '{}', '{}', '{}')
                        ;'''.format(id, code, h1, title, description, date1))
            cursor.execute("SELECT * FROM url_checks WHERE url_id = '{}'".format(id))
            checks = cursor.fetchall()
            flash('Страница успешно проверена', 'success')
        except Exception:
            checks = []
            flash('Произошла ошибка при проверке', 'error')
    return render_template(
        'urls_id.html',
        id=id,
        name=name,
        created_at=created_at,
        checks=checks
    )
