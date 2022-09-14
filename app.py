from flask import Flask, render_template, request, redirect, Blueprint, flash, url_for
from flask_oidc import OpenIDConnect
import socket
import os
import re
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user
)
from oauth2client.client import OAuth2Credentials
from db import init_db_command
from user import User

app = Blueprint('app', __name__, template_folder='templates')

from Web_app.subscription import subscription, createRequest
from Web_app.data_ingestion import data_ingestion
from Web_app.view_history import view_history
from Web_app.decoratorApp import decoratorCheckAppOrg
from Web_app.profile import profile

app = Flask(__name__)

app.config.update({
    'SECRET_KEY': 'SomethingNotEntirelySecret',
    'TESTING': True,
    'DEBUG': True,
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
    #'OIDC_CALLBACK_ROUTE': '',
    'OVERWRITE_REDIRECT_URI':'https://10.10.10.13:5007/*',
    'OIDC_ID_TOKEN_COOKIE_SECURE': False,
    'OIDC_REQUIRE_VERIFIED_EMAIL': False,
    'OIDC_USER_INFO_ENABLED': True,
    'OIDC_OPENID_REALM': 'master',
    'OIDC_SCOPES': ['openid', 'email', 'profile'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post'
})

oidc = OpenIDConnect(app)

app.register_blueprint(subscription)
app.register_blueprint(data_ingestion)
app.register_blueprint(view_history)
app.register_blueprint(profile)

#User session management setup
login_manager = LoginManager()
login_manager.init_app(app)

#we assume that app.py and sqlite_db are on the same directory
#initialize db only if it does not exist yet
if 'sqlite_db' not in os.listdir("sqlite_data/"):
    init_db_command()

#Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Upload folder
UPLOAD_FOLDER = 'static/json'
app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER

@app.route('/')
@decoratorCheckAppOrg
def index():
    if current_user.is_authenticated:
        #Successfully authenticated
        token = User.get_field("id", current_user.id, "user", "token")
        return render_template('main.html', name = current_user.name, email = current_user.email, tkn = token)
    else:
        return render_template('index.html')

# @app.route('/bbbb', methods= ["GET"])
# @decoratorCheckAppOrg
# def custom_callback():
#     info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
#     unique_id = info.get('sub')
#     user_email = info.get('email')
#     user_name = info.get('preferred_username')

#     if unique_id in oidc.credentials_store:
#         token = OAuth2Credentials.from_json(oidc.credentials_store[unique_id]).access_token

#     user = User(
#     id_=unique_id, name=user_name, email=user_email, token=token, organization=None, domain_name=None
#     )
#     # Doesn't exist? Add it to the database.
#     if not User.get(unique_id): 
#         User.create(unique_id, user_name, user_email, token, None, None)
#     else:
#         User.update_field("id", unique_id, "user", "token", token)
#     login_user(user)
#     return render_template('main.html', name = current_user.name, email = current_user.email, tkn = token)

@app.route('/login', methods=["GET"])
@oidc.require_login
def login():
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    unique_id = info.get('sub')
    user_email = info.get('email')
    user_name = info.get('preferred_username')

    if unique_id in oidc.credentials_store:
        token = OAuth2Credentials.from_json(oidc.credentials_store[unique_id]).access_token

    user = User(
    id_=unique_id, name=user_name, email=user_email, token=token, organization=None, domain_name=None
    )
    # Doesn't exist? Add it to the database.
    if not User.get(unique_id): 
        User.create(unique_id, user_name, user_email, token, None, None)
    else:
        User.update_field("id", unique_id, "user", "token", token)
    login_user(user)
    return render_template('main.html', name = current_user.name, email = current_user.email, tkn = token)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    oidc.logout()
    return redirect("/")

@app.route('/push_app_org', methods= ["POST"])
def push_app_org():
    if not current_user.is_authenticated:
        flash('You should login first!', 'error')
        return index()
    org = request.values.get('org')
    domain_name = request.form['domain_name']
    app_list=[]
    i=1
    appl = request.form.get("app"+str(i))
    while appl!=None:
        if re.match("^[a-zA-Z0-9_]+$", str(appl)):
            if appl not in app_list:
                app_list.append(appl)
        else:
            message = "Application name not allowed. You can use the following characters: [a-z], [A-Z], [0-9] and _"
            return render_template('modal.html', message=message)
        i += 1
        appl = request.form.get("app"+str(i))
    User.update_field("id", current_user.id, "user", "organization", org)
    User.update_field("id", current_user.id, "user", "domain_name", domain_name)
    #when a new user-app entry is created in the apps db, a new subscription must be created to QL
    for appl in app_list:
        User.create_user_app(appl, current_user.id)
    for appl in app_list:
        if appl not in User.get_all("apps", "name"):
            #create subscription to notify quantumleap in order to data in crateDB
            createRequest(appl, "http://quantumleap:8668/v2/notify")
    return redirect("/")
# EDW TI FASH?????
if __name__ == "__main__":
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(ssl_context="adhoc", host=ipV4IP, port=5007)