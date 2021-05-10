from flask import Flask, render_template, request, redirect, url_for
import os
import requests
import json
import sqlite3
from os.path import join, dirname, realpath
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

# Configure Keyrock as the IDM
KEYROCK_CLIENT_ID = os.environ.get("KEYROCK_CLIENT_ID", None)
print(KEYROCK_CLIENT_ID)
KEYROCK_CLIENT_SECRET = os.environ.get("KEYROCK_CLIENT_SECRET", None)
KEYROCK_DISCOVERY_URL = (
    "https://account.lab.fiware.org"
    #"http://192.168.56.102:3443/idm"
)

# Referencing the file __name__

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

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
#LLOWED_EXTENSIONS = {'json', 'csv'}

app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER

@app.route('/', methods= ["GET", "POST"])
def index():
    if current_user.is_authenticated:
        #"Successfully authenticated. <br><br> <br><br><button onclick='window.location.href=\"/user_info\"'>Get my user info</button>"
        #print("I'm here:", current_user.name, current_user.email)
        #upload_file()
        return render_template('upload.html', name = current_user.name, email = current_user.email)
    else:
        return render_template('index.html')
        #return "Oauth2 IDM Demo.<br><br><button onclick='window.location.href=\"/auth\"'>Log in with Keyrock Account</button><br><br><button onclick='window.location.href=\"/authJWT\"'>Log in with Keyrock Account and JWT</button>'

'''@app.route('/upload', methods= ['POST'])
def upload_file():
    return render_template('upload_jsonfile.html')'''

"""def upload_file():
    if request.method == "POST":
        file1 = request.files["jsonFile"]
        filename = secure_filename(file1.filename)
        file1.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return render_template('displayJson.html')
    else:
        return render_template('upload_jsonfile.html')"""

@app.route('/login')
def login():
    # Find out what URL to hit for Google login
    authorization_endpoint = KEYROCK_DISCOVERY_URL+'/oauth2/authorize'
    #print(request.base_url+ "/callback")
    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    #print(request_uri)
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Keyrock sent back to you
    code = request.args.get("code")
    #print("Code:", code)
    token_endpoint = KEYROCK_DISCOVERY_URL+'/oauth2/token'
    #print("This is the base url:", request.base_url)
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    #print("Token_url:", token_url, "headers:", headers)
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(KEYROCK_CLIENT_ID, KEYROCK_CLIENT_SECRET)
    )
    # Parse the tokens!
    #print("Parse the tokens:", client.parse_request_body_response(json.dumps(token_response.json())))
    client.parse_request_body_response(json.dumps(token_response.json()))
    return redirect(url_for("get_user_info"))

@app.route("/user_info")
def get_user_info():
    userinfo_endpoint = KEYROCK_DISCOVERY_URL+'/user'
    uri, headers, body = client.add_token(userinfo_endpoint)
    #print("AUTA:", uri, headers, body)

    token = headers['Authorization'].split(' ')[1]
    #print("Token:", token)
    uri2 = 'https://account.lab.fiware.org/user?access_token=' + token
    #print("uri2=", uri2)
    userinfo_response = requests.get(uri2)
    #print("HERE:", userinfo_response.json())

    unique_id = userinfo_response.json()["id"]
    user_email = userinfo_response.json()["email"]
    user_name = userinfo_response.json()["displayName"]

    user = User(
    id_=unique_id, name=user_name, email=user_email
    )

    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, user_name, user_email)

    print("The user:", user)
    login_user(user)
    return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

if __name__ == "__main__":
    # app.run(debug=True)
    app.run(debug=True, ssl_context="adhoc")