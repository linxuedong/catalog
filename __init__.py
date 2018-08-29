from flask import (Flask, render_template, request, redirect,
                   url_for, flash, make_response, abort)
from flask import session as login_session

import jwt
import datetime
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from .models import Base
from .models import Category, Item, User

from google.oauth2 import id_token
from google.auth.transport import requests

app = Flask(__name__)
app.config.from_pyfile('config.py')

engine = create_engine('postgresql://vagrant@localhost/catalog')
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)

CLIENT_ID = json.loads(
    open('catalog/client_secret.json', 'r').read())['web']['client_id']


@app.route('/login')
def login():
    exp = datetime.datetime.utcnow() + datetime.timedelta(seconds=30)
    permission = {'can_add': True, 'can_edit': True,
                  'can_delete:': True, 'exp': exp}
    state = jwt.encode(permission, 'secret', algorithm='HS256').decode('utf-8')
    login_session['state'] = state
    return render_template('login.html', STATE=state, exp=exp)


@app.route('/logout')
def logout():
    login_session['username'] = None
    login_session['picture'] = None
    login_session['email'] = None
    login_session['state'] = None
    login_session['user_id'] = None
    flash('Logout successfully!')
    return render_template('logout.html')


@app.route('/gconnect', methods=['GET', 'POST'])
def gconnect():
    # Validate state token

    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    token = request.data

    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), CLIENT_ID)

        # Or, if multiple clients access the backend server:
        # idinfo = id_token.verify_oauth2_token(token, requests.Request())
        # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
        #     raise ValueError('Could not verify audience.')

        google_api = 'https://accounts.google.com'
        if idinfo['iss'] not in ['accounts.google.com', google_api]:
            raise ValueError('Wrong issuer.')

        # If auth request is from a G Suite domain:
        # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
        #     raise ValueError('Wrong hosted domain.')

        # ID token is valid. Get the user's Google Account ID from the decoded
        # token.
        # userid = idinfo['sub']
    except ValueError:
        # Invalid token
        raise ValueError('Invalid token.')
    login_session['username'] = idinfo['name']
    login_session['email'] = idinfo['email']
    login_session['picture'] = idinfo['picture']

    user_id = get_user_id(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    flash("you are now logged in as %s" % login_session['username'])

    return login_session['username']


def create_user(login_session):
    name = login_session['username']
    email = login_session['email']
    picture = login_session['picture']
    new_user = User(name=name, email=email, picture=picture)
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(name=name).one()
    return user.id


def get_user_info(user_id):
    user = session.query(User).get(user_id)
    return user


def get_user_id(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except NoResultFound:
        return None


@app.route('/')
def index():
    # 展示 categories
    categories = session.query(Category).all()

    # 展示 items
    items = session.query(Item).order_by(Item.created_at.desc()).all()

    return render_template('index.html', categories=categories, items=items)


@app.route('/catalog/<category_name>/items')
def item_list(category_name):
    # categories
    categories = session.query(Category).all()
    current_category = session.query(Category).filter(
        Category.name == category_name).one()

    # 某个 categories 的 items
    items = session.query(Item).filter(
        Item.category == current_category
    ).order_by(Item.created_at.desc()).all()

    return render_template('index.html', categories=categories, items=items)


@app.route('/catalog/<category_name>/<item_name>')
def item_detail(category_name, item_name):
    item = session.query(Item).filter(Item.title == item_name).one()
    operate = True
    if item.user.id != login_session['user_id']:
        operate = False
    return render_template('item_detail.html', item=item, operate=operate)


def auth_author(item):
    if item.user.id != login_session['user_id']:
        abort(404)


@app.route('/catalog/<item_name>/edit', methods=['GET', 'POST'])
def edit(item_name):
    categories = session.query(Category).all()
    item_query = session.query(Item).filter(Item.title == item_name)
    item = item_query.one()

    auth_author(item)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category_id = str(request.form['category'])

        new_item = {
            'title': title,
            'description': description,
            'category_id': category_id
        }

        item_query.update(new_item)
        session.commit()

        flash('You were successfully edited.')

        return redirect(url_for(
            'item_detail', category_name=item.category.name, item_name=title))
    return render_template('edit.html', categories=categories, item=item)


@app.route('/catalog/<item_name>/delete', methods=['GET', 'POST'])
def delete(item_name):
    item_query = session.query(Item).filter(Item.title == item_name)
    item = item_query.one()
    auth_author(item)
    if request.method == 'POST':
        item_query.delete()
        session.commit()
        flash('You were successfully deleted.')

        return redirect(url_for('index'))

    return render_template('delete_item.html', item=item)
