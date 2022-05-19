from flask import Flask, render_template, request, redirect, url_for, Blueprint, flash
import socket
import os
import requests
import json
import sqlite3
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user
)
from oauthlib.oauth2 import WebApplicationClient

from db import init_db_command
from user import User

# Configure Keyrock as the IDM
KEYROCK_CLIENT_ID = os.environ.get("KEYROCK_CLIENT_ID")
KEYROCK_CLIENT_SECRET = os.environ.get("KEYROCK_CLIENT_SECRET")

KEYROCK_DISCOVERY_URL = (
    "https://cloud-20-nic.8bellsresearch.com:443"
)

app = Blueprint('app', __name__, template_folder='templates')

# Referencing the file __name__
#from consumer import consumers
from subscription import subscription, createRequest, sendRequestToFiware
from data_ingestion import data_ingestion
from view_history import view_history
from decoratorApp import decoratorCheckAppOrg

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

@app.route('/', methods= ["GET"])
@decoratorCheckAppOrg
def index():
    if current_user.is_authenticated:
        #Successfully authenticated
        token = User.get_field(current_user.id, "user", "token")
        return render_template('main.html', name = current_user.name, email = current_user.email, tkn = token)
    else:
        return render_template('index.html')

@app.route('/push_app_org', methods= ["POST"])
def push_app_org():
    if not current_user.is_authenticated:
        flash('You should login first!', 'error')
        return index()
    appl = request.form['application']
    org = request.values.get('org')
    domain_name = request.form['domain_name']
    User.add_app_org(current_user.id, appl, org)
    User.update_field(current_user.id, "user", "domain_name", domain_name)
    if appl not in User.fetch_applications():
        #create subscription to notify quantumleap in order to data in crateDB
        createRequest(appl, "http://quantumleap:8668/v2/notify")
    return redirect("/")

@app.route('/login')
def login():
    # Find out what URL to hit for Keyrock login
    authorization_endpoint = KEYROCK_DISCOVERY_URL + '/oauth2/authorize'
    print("Within login", request.base_url+ "/callback")
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri= request.base_url + "/callback", #"https://jenkins.8bellsresearch.com:443/login/callback"
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
        redirect_url= request.base_url,#"https://jenkins.8bellsresearch.com:443/login/callback"
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
    # if not current_user.is_authenticated:
    #     flash('You should login first!', 'error')
    #     return index()
    userinfo_endpoint = KEYROCK_DISCOVERY_URL+'/user'
    uri, headers, body = client.add_token(userinfo_endpoint)
    token = headers['Authorization'].split(' ')[1]
    uri2 = KEYROCK_DISCOVERY_URL + "/user?access_token=" + token
    userinfo_response = requests.get(uri2, verify=False)
    unique_id = userinfo_response.json()["id"]
    user_email = userinfo_response.json()["email"]
    user_name = userinfo_response.json()["username"]

    user = User(
    id_=unique_id, name=user_name, email=user_email, token=token, application=None, organization=None, domain_name=None
    )
    # Doesn't exist? Add it to the database.
    if not User.get(unique_id): 
        User.create(unique_id, user_name, user_email, token, None, None, None)
    else:
        User.update_field(unique_id, "user", "token", token)
    login_user(user)
    return redirect("/")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == "__main__":
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(ssl_context="adhoc", host=ipV4IP)