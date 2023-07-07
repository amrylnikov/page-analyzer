import psycopg2
from datetime import date
import requests
from bs4 import BeautifulSoup
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

connection = psycopg2.connect(
    dbname="alex",
    user="name",
    password="pass",
    host="127.0.0.1")
connection.autocommit = True

app = Flask(__name__)
app.secret_key = "secret_key"


@app.route('/')
def index():
    return render_template('index.html')

# DISTINCT urls.id, urls.name, urls.created_at, url_checks.created_at, url_checks.status_code
@app.get('/urls') 
def urls_display():
    cursor = connection.cursor()
    cursor.execute("""
                   SELECT DISTINCT urls.id, urls.name, urls.created_at, url_checks.created_at, url_checks.status_code
                   FROM urls
                   LEFT JOIN url_checks ON url_checks.url_id = urls.id
                   """)
    urls = cursor.fetchall()
    cursor.close()
    return render_template(
        '/urls.html',
        urls=urls
    )


@app.post('/urls')
def urls_add():
    url_name = request.form.get('url')
    print('Url = ', url_name)
    errors = validate(url_name)
    if errors:
        return render_template(
            'index.html',
            url_name=url_name,
            errors=errors,
        ), 422
    if url_name[-1:] == '/':
        url_name = url_name[:-1]
    date1 = date.today()
    print('Date: = ', date1)
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM urls WHERE name = '{}'".format(url_name))
    temp = cursor.fetchone()
    if temp:
        if url_name == temp[0]:
            cursor.execute("SELECT id FROM urls WHERE name = '{}'".format(url_name))
            id_temp = cursor.fetchone()[0]
            cursor.close()
            flash('Страница уже существует', 'info')
            return redirect(url_for('url_info', id=id_temp))
    cursor.execute("INSERT INTO urls (name, created_at) VALUES ('{}', '{}');".format(url_name, date1))
    cursor.execute("SELECT id FROM urls WHERE name = '{}' AND created_at = '{}' ORDER BY id DESC".format(url_name, date1))
    id_temp = cursor.fetchone()[0]
    print('ID = ', id_temp)
    cursor.close()
    # user['id'] = ShortUUID().random(length=7)
    # save_user(user)
    # with open('users.json', 'r') as f:
    #     users = [json.loads(line.strip()) for line in f]
    # flash('User was added successfully!', 'success')
    # messages = get_flashed_messages(with_categories=True)
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('url_info', id=id_temp))


@app.route('/urls/<id>')
def url_info(id):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM urls WHERE id = '{}'".format(id))
    temp = cursor.fetchone()
    cursor.execute("SELECT * FROM url_checks WHERE url_id = '{}'".format(id))
    checks = cursor.fetchall()
    cursor.close()
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
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT name FROM urls WHERE id = '{}'".format(id))
        name = cursor.fetchone()[0]
        r = requests.get(name)
        print('STATUS CODE: ', r.status_code)
        code = r.status_code
        soup = BeautifulSoup(r.text, 'html.parser')
        h1_tags = soup.find_all('h1')
        title = soup.title.get_text()
        h1_answer = ''
        for h1 in h1_tags:
            h1_text = h1.get_text()
            h1_answer += str(h1_text)
        meta_tags = soup.find_all('meta')
        description = ''
        for meta in meta_tags:
            if meta.get('name') == 'description':
                site_description = meta.get('content')
                description += site_description
        date1 = date.today()
        cursor.execute('''INSERT INTO url_checks
                    (url_id, status_code, h1, title, description, created_at)
                    VALUES ('{}', '{}', '{}', '{}', '{}', '{}')
                    ;'''.format(id, code, h1_answer, title, description, date1))
        cursor.execute("SELECT * FROM url_checks WHERE url_id = '{}'".format(id))
        checks = cursor.fetchall()
        flash('Страница успешно проверена', 'success')
    
    except:
        flash('Произошла ошибка при проверке', 'error')
        checks=[]
    
    cursor.execute("SELECT * FROM urls WHERE id = '{}'".format(id))
    temp = cursor.fetchone()
    cursor.close()
    name = temp[1]
    created_at = temp[2]
    
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'urls_id.html',
        id=id,
        name=name,
        created_at=created_at,
        messages=messages,
        checks=checks
    )
