from flask import (
    Flask,
    flash,
    get_flashed_messages,
    render_template,
    request,
    redirect,
    url_for
)
import os, json
import uuid
from shortuuid import ShortUUID

app = Flask(__name__)
app.secret_key = "secret_key"


@app.route('/')
def hello_world():
    cart = json.loads(request.cookies.get('cart', json.dumps({})))
    return render_template('index.html', cart=cart)


@app.get('/users')
def user_intro():
    cart = json.loads(request.cookies.get('cart', json.dumps({})))
    with open('users.json', 'r') as f:
        users = [json.loads(line.strip()) for line in f]
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        '/users/index.html',
        users=users,
        messages=messages,
        cart=cart
    )


@app.post('/users')
def user_update():
    user = request.form.to_dict()
    user['id'] = ShortUUID().random(length=7)
    save_user(user)
    with open('users.json', 'r') as f:
        users = [json.loads(line.strip()) for line in f]
    flash('User was added successfully!', 'success')
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        '/users/index.html',
        users=users,
        messages=messages
    )


def save_user(user):
    with open('users.json', 'a') as f:
        f.write(json.dumps(user) + '\n')


@app.route('/users/new')
def user_getting():
    user = {'id': '',
            'name': '',
            'email': ''}
    return render_template(
        '/users/new.html',
        user=user
    )


@app.route('/users/<id>')
def user_info(id):
    with open('users.json', 'r') as f:
        users = [json.loads(line.strip()) for line in f]
    for expexted_user in users:
        if str(id) == expexted_user['id']:
            user = expexted_user
    if not user:
        return 'Page not found', 404
    
    return render_template(
        'users/show.html',
        user=user
    )

@app.route('/users/<id>/edit')
def edit_user(id):
    with open('users.json', 'r') as f:
        users = [json.loads(line.strip()) for line in f]
    for expexted_user in users:
        if str(id) == expexted_user['id']:
            user = expexted_user
    
    return render_template(
        'users/edit.html',
        user=user
    )


@app.route('/users/<id>/patch', methods=['POST'])
def patch_user(id):
    data = request.form.to_dict()
    with open('users.json', 'r') as f:
        users = [json.loads(line.strip()) for line in f]
    for expexted_user in users:
        if str(id) == expexted_user['id']:
            expexted_user['name'] = data['name']
            expexted_user['email'] = data['email']
    with open('users.json', 'w') as f:
        for user in users:
            json.dump(user, f)
            f.write('\n')
    # Ручное копирование данных из формы в нашу сущность
    flash('User has been updated', 'success')
    return redirect(url_for('user_intro'))


@app.route('/users/<id>/delete', methods=['POST'])
def delete_user(id):
    with open('users.json', 'r') as f:
        users = [json.loads(line.strip()) for line in f]
    new_users = [d for d in users if d['id'] != str(id)]
    print('HERE IT IS')
    print(new_users)
    print('HERE IT IS')
    print(users)
    print('HERE IT IS')
    with open('users.json', 'w') as f:
        for user in new_users:
            json.dump(user, f)
            f.write('\n')
    
    flash('User has been deleted', 'success')
    return redirect(url_for('user_intro'))
