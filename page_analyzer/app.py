import logging
import os
from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg2
import requests
from dotenv import load_dotenv
from flask import (Flask, abort, flash, redirect, render_template, request,
                   url_for)

from page_analyzer import db, html
from page_analyzer.validator import validate

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
TIMEOUT = int(os.getenv('EXTERNAL_REQUEST_TIMEOUT', 30))
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')


@contextmanager
def connect(bd_url):
    try:
        connection = psycopg2.connect(bd_url)
        yield connection
    except Exception:
        if connection:
            connection.rollback()
        raise
    else:
        if connection:
            connection.commit()
    finally:
        if connection:
            connection.close()


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    logging.exception(str(e))
    return render_template('500.html'), 500


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def urls_list():
    with connect(DATABASE_URL) as conn:
        urls = db.get_all_urls(conn)
        url_checks = {item.url_id: item for item in db.get_all_url_checks(conn)}
    return render_template(
        '/urls.html',
        urls=urls,
        url_checks=url_checks
    )


@app.post('/urls')
def url_add():
    url_name = request.form.get('url')
    errors = validate(url_name)
    if errors:
        for error in errors:
            flash(error, 'error')
        return render_template(
            'index.html',
        ), 422
    url_parsed = urlparse(url_name)
    url_name = f'{url_parsed.scheme}://{url_parsed.netloc}'
    with connect(DATABASE_URL) as conn:
        url_to_check = db.get_url_by_name(conn, url_name)
        if url_to_check:
            flash('Страница уже существует', 'info')
            return redirect(url_for('url_info', id=url_to_check[0]))
        url_id = db.create_url(conn, url_name)
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('url_info', id=url_id))


@app.get('/urls/<id>')
def url_info(id):
    with connect(DATABASE_URL) as conn:
        url = db.get_url_by_id(conn, id)
        if not url:
            abort(404)
        name = url.name
        created_at = url.created_at
        url_checks = db.get_checks_by_url_id(conn, id)
    return render_template(
        'urls_id.html',
        id=id,
        name=name,
        created_at=created_at,
        checks=url_checks
    )


@app.post('/urls/<id>/checks')
def url_check(id):
    with connect(DATABASE_URL) as conn:
        url = db.get_url_by_id(conn, id)
        if not url:
            abort(404)
        name = url.name
        try:
            request = requests.get(name, timeout=TIMEOUT)
            request.raise_for_status()
        except requests.RequestException:
            flash('Произошла ошибка при проверке', 'error')
            return redirect(url_for('url_info', id=id))
        status_code = request.status_code
        h1, title, description = html.get_seo_data(request.text)
        db.create_check(conn, id, status_code, h1, title, description)
    flash('Страница успешно проверена', 'success')
    return redirect(url_for('url_info', id=id))
