import os
from contextlib import contextmanager
from datetime import date
from urllib.parse import urlparse

import psycopg2
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from flask import (Flask, abort, flash, redirect, render_template, request,
                   url_for)

from page_analyzer import db
from page_analyzer.functions import parse_seo_content
from page_analyzer.validator import validate

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
        yield connection
    finally:
        connection.close()


@app.route('/')
def index():
    return render_template('index.html')


# url_lists
@app.get('/urls')
def urls_display():
    with connect(DATABASE_URL) as conn:
        urls = db.get_sites(conn)
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
    # creation_date под капот
    creation_date = date.today()
    with connect(DATABASE_URL, True) as conn:
        id = db.get_url_id_by_name(conn, url_name)
        if id:
            flash('Страница уже существует', 'info')
            return redirect(url_for('url_info', id=id[0]))
        id = db.create_url(conn, url_name, creation_date)
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('url_info', id=id))


@app.route('/urls/<id>')
def url_info(id):
    with connect(DATABASE_URL) as conn:        
        url = db.get_url_by_id(conn, id)
        if not url:
            abort(404)
        name = url[1]
        created_at = url[2]
        checks = db.get_url_checks_by_id(conn, id)
    return render_template(
        'urls_id.html',
        id=id,
        name=name,
        created_at=created_at,
        checks=checks
    )


@app.route('/urls/<id>/checks', methods=['GET', 'POST'])
def url_check(id):
    with connect(DATABASE_URL, True) as conn:
        url = db.get_url_by_id(conn, id)
        if not url:
            abort(404)
        name = url[1]
        created_at = url[2]
        try:
            # r -> response
            # логировать чтобы понимать что происходит с приложением. В опасных местах. Важные переменные и т.д.
            # Например этот реквест
            request = requests.get(name)
            # вынести за трай парсинк и ифы
            # И вместо чексов он делает редирект в каждом месте flash.
            code = request.status_code
            soup = BeautifulSoup(request.text, 'html.parser')
            h1, title, description = parse_seo_content(soup)
            if code != 200:
                checks = []
                flash('Произошла ошибка при проверке', 'error')
            else:
                date1 = date.today()
                checks = db.create_check(conn, id, code, h1, title, description, date1)
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
