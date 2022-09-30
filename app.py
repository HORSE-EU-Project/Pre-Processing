from flask import Flask, render_template, request, redirect, Blueprint, flash, url_for, session
import socket
import os
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user
)
from db import init_db_command
from user import User
from keycloak_requests import get_kc_token, get_kc_userinfo

app = Blueprint('app', __name__, template_folder='templates')

from Web_app.subscription import subscription, createRequest
from Web_app.data_ingestion import data_ingestion
from Web_app.view_history import view_history
from Web_app.decoratorApp import decoratorCheckAppOrg
from Web_app.profile import profile

app = Flask(__name__)

app.config.update({
    'SECRET_KEY': 'kEGoPX0E5Pn18ZY5EXCKtW1TUTjeY5c8',
    'TESTING': True,
    'DEBUG': True
})

app.register_blueprint(subscription)
app.register_blueprint(data_ingestion)
app.register_blueprint(view_history)
app.register_blueprint(profile)

#User session management setup
login_manager = LoginManager()
login_manager.init_app(app)

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

@app.route('/', methods= ['GET', 'POST'], endpoint='index')
@decoratorCheckAppOrg
def index():
    if current_user.is_authenticated:
        #Successfully authenticated
        token = User.get_field("id", current_user.id, "user", "token")
        return render_template('main.html', name = current_user.name, email = current_user.email, tkn = token)
    else:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            # flash('Invalid credentials: ' + username + password + '!', 'error')   
            # return render_template('index.html')
            response = get_kc_token(username, password)
            if response.status_code != 200:
                flash('We got: ' + str(response.status_code) + 'from Keycloak.', 'error')
                return render_template('index.html')
            token = response.json()["access_token"]
            session["messages"] = token
            return redirect(url_for('get_userinfo', messages=token))
        else:
            return render_template('index.html')

@app.route('/get_userinfo', methods=["GET"], endpoint='get_userinfo')
@decoratorCheckAppOrg
def get_userinfo():
    token = request.args['messages']
    response = get_kc_userinfo(token)
    if response.status_code != 200:
        flash('Keycloak is not responding. Status code: ' + response.status_code + ' Try again later!', 'error')
        return render_template('index.html')
    user_name = response.json()["preferred_username"]
    user_email = response.json()["email"]
    unique_id = response.json()["sub"]
    user = User(
    id_=unique_id, name=user_name, email=user_email, token=token, organization=None, domain_name=None
    )
    # Doesn't exist? Add it to the database.
    if not User.get(unique_id): 
        User.create(unique_id, user_name, user_email, token, None, None)
    else:
        User.update_field("id", unique_id, "user", "token", token)
    login_user(user)
    return redirect('/home')

@app.route('/home', endpoint='home')
@decoratorCheckAppOrg
def home():
    return render_template('main.html', name = current_user.name, email = current_user.email, tkn = current_user.token)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == "__main__":
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(ssl_context="adhoc", host=ipV4IP, port=5005)