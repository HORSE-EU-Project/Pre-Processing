from asyncio.windows_events import NULL
from flask import Flask, render_template, request, redirect, url_for, Blueprint
import socket
import os
import requests
import json
import sqlite3
from os.path import join, dirname, realpath
from requests.sessions import requote_uri, session
from werkzeug.utils import secure_filename
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
    UserMixin
)
from oauthlib.oauth2 import WebApplicationClient

from db import init_db_command
from user import User

#import socket

global index_add_counter #for test
index_add_counter=0 #for test

# Configure Keyrock as the IDM
KEYROCK_CLIENT_ID = os.environ.get("KEYROCK_CLIENT_ID", "23a8072b-5fd2-412d-b485-287243c5e486")
KEYROCK_CLIENT_SECRET = os.environ.get("KEYROCK_CLIENT_SECRET", "79745999-794b-46a1-9c59-8508c9a96c63")
KEYROCK_DISCOVERY_URL = (
    #"https://account.lab.fiware.org"
    "https://10.0.18.77:443"
)

app = Blueprint('app', __name__, template_folder='templates')

# Referencing the file __name__
#from consumer import consumer
from subscription import subscription
from data_ingestion import data_ingestion
from view_history import view_history

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
app.register_blueprint(subscription)
app.register_blueprint(data_ingestion)
app.register_blueprint(view_history)

# User session management setup
login_manager = LoginManager()
login_manager.init_app(app)

# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# OAuth 2 client setup
client = WebApplicationClient(KEYROCK_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Upload folder
UPLOAD_FOLDER = 'static/json'
app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER

def decoratorCheckAppOrg(func):
    def inner():
        if User.get_app(current_user.id)==NULL or User.get_org(current_user.id)==NULL:
            return render_template('modal.html' , name = current_user.name, email = current_user.email)
        else:
            view = func()
            return view
    return inner

@app.route('/', methods= ["GET", "POST"])
@decoratorCheckAppOrg
def index():
    if current_user.is_authenticated:
        #Successfully authenticated
        
        token = User.get_token(current_user.id) 

        global index_add_counter #for test
        index_add_counter=index_add_counter+1 #for test

        if index_add_counter==1: #for test
            return render_template('modal.html' , name = current_user.name, email = current_user.email)
        else:
            return render_template('main.html', name = current_user.name, email = current_user.email, tkn = token)
    else:
        return render_template('index.html')


@app.route('/login')

def login():
    # Find out what URL to hit for Keyrock login
    authorization_endpoint = KEYROCK_DISCOVERY_URL + '/oauth2/authorize' #'/v1/auth'
    #print(request.base_url+ "/callback")
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        state="xyz",
        scope=["openid", "email", "profile"],
        #prompt='login',
        verify=False,
    
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Keyrock sent back to you
    code = request.args.get("code")
    token_endpoint = KEYROCK_DISCOVERY_URL+'/oauth2/token'
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        #prompt='login',
        code=code
    )
 
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(KEYROCK_CLIENT_ID, KEYROCK_CLIENT_SECRET),
        verify=False
    )
    # Parse the tokens!

    client.parse_request_body_response(json.dumps(token_response.json()))
    return redirect(url_for("get_user_info"))

@app.route("/user_info")
def get_user_info():
    userinfo_endpoint = KEYROCK_DISCOVERY_URL+'/user'
    uri, headers, body = client.add_token(userinfo_endpoint)
    token = headers['Authorization'].split(' ')[1]
    uri2 = KEYROCK_DISCOVERY_URL + "/user?access_token=" + token
    userinfo_response = requests.get(uri2, verify=False)
    unique_id = userinfo_response.json()["id"]
    user_email = userinfo_response.json()["email"]
    user_name = userinfo_response.json()["username"]

    user = User(
    id_=unique_id, name=user_name, email=user_email, token=token
    )
    # Doesn't exist? Add it to the database.
    if not User.get(unique_id): 
        User.create(unique_id, user_name, user_email, token)
    else:
        User.updateToken(unique_id, token)
    login_user(user)
    return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == "__main__":
    # app.run(debug=True)
    ipV4IP = socket.gethostbyname(socket.gethostname())
    print(ipV4IP)
    app.run(debug=True, ssl_context="adhoc", host=ipV4IP)

