import psycopg2
from flask import (
    Flask,
    flash,
    get_flashed_messages,
    render_template,
    request,
    redirect,
    url_for
)
from datetime import date
from page_analyser.validator import validate



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


@app.get('/urls')
def urls_display():

    return render_template(
        '/urls.html'
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
    date1 = date.today()
    print('Date: = ', date1)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO urls (name, created_at) VALUES ('{}', '{}');".format(url_name, date1))
    # cursor.execute("SELECT * FROM urls;")
    # print(cursor.fetchone())
    cursor.close()
    # user['id'] = ShortUUID().random(length=7)
    # save_user(user)
    # with open('users.json', 'r') as f:
    #     users = [json.loads(line.strip()) for line in f]
    # flash('User was added successfully!', 'success')
    # messages = get_flashed_messages(with_categories=True)
    return render_template(
        '/urls.html',
        # users=users,
        # messages=messages
    )


@app.route('/urls/<id>')
def url_info(id):


    return render_template(
        'users/show.html',
        user=user
    )
