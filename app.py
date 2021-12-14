from flask import Flask, render_template, request, redirect, url_for, Blueprint
import socket
import os
import requests
import json
import sqlite3
from os.path import join, dirname, realpath
from requests.sessions import session
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

# Configure Keyrock as the IDM
KEYROCK_CLIENT_ID = os.environ.get("KEYROCK_CLIENT_ID", None)
KEYROCK_CLIENT_SECRET = os.environ.get("KEYROCK_CLIENT_SECRET", None)
KEYROCK_DISCOVERY_URL = (
    #"https://account.lab.fiware.org"
    "https://10.0.20.226:443"
)

''' hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

print(local_ip) '''

app = Blueprint('app', __name__, template_folder='templates')

# Referencing the file __name__
#from consumer import consumer
from registerb import registerb
from subscription import subscription

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
#app.register_blueprint(consumer)
app.register_blueprint(registerb)
app.register_blueprint(subscription)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
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

@app.route('/', methods= ["GET", "POST"])
def index():
    if current_user.is_authenticated:
        #Successfully authenticated
        
        token = User.get_token(current_user.id)
        return render_template('main.html', name = current_user.name, email = current_user.email, tkn = token)
    else:
        return render_template('index.html')
        #return "Oauth2 IDM Demo.<br><br><button onclick='window.location.href=\"/auth\"'>Log in with Keyrock Account</button><br><br><button onclick='window.location.href=\"/authJWT\"'>Log in with Keyrock Account and JWT</button>'


@app.route('/login')
def login():
    # Find out what URL to hit for Google login
    authorization_endpoint = KEYROCK_DISCOVERY_URL + '/oauth2/authorize' #'/v1/auth'
    #print(request.base_url+ "/callback")
    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        state="xyz",
        scope=["openid", "email", "profile"],
        #prompt='login',
        verify=False,
    )
    #print(request_uri)
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Keyrock sent back to you
    code = request.args.get("code")
    #print(code)
    token_endpoint = KEYROCK_DISCOVERY_URL+'/oauth2/token'
    #print("This is the base url:", request.base_url)
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        #prompt='login',
        code=code
    )
    #print("Token_url:", token_url, "headers:", headers, "Body:", body)
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(KEYROCK_CLIENT_ID, KEYROCK_CLIENT_SECRET),
        verify=False
    )
    # Parse the tokens!
    #print("Parse the tokens:", client.parse_request_body_response(json.dumps(token_response.json())))
    client.parse_request_body_response(json.dumps(token_response.json()))
    return redirect(url_for("get_user_info"))

@app.route("/user_info")
def get_user_info():
    userinfo_endpoint = KEYROCK_DISCOVERY_URL+'/user'
    uri, headers, body = client.add_token(userinfo_endpoint)
    token = headers['Authorization'].split(' ')[1]
    #uri2 = 'https://account.lab.fiware.org/user?access_token=' + token
    uri2 = "https://10.0.20.226:443/user?access_token=" + token
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
    #requests.post(KEYROCK_DISCOVERY_URL+"/oauth2/logout?client_id="+KEYROCK_CLIENT_ID, verify=False)
    return redirect(url_for('index'))

if __name__ == "__main__":
    # app.run(debug=True)
    ipV4IP = socket.gethostbyname(socket.gethostname())
    print(ipV4IP)
    app.run(debug=True, ssl_context="adhoc", host="192.168.192.64")
    #"172.20.23.207"