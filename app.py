from flask import Flask, render_template, request, redirect, Blueprint, flash, url_for, session, current_app
#from flask_mail import Mail
import socket
import os
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user
)
from db import init_db_command, update_db_schema_command, drop_table
from user import User
from keycloak_requests import get_kc_token, get_kc_userinfo
import secrets
app = Flask(__name__ , template_folder='templates') 
secret = secrets.token_urlsafe(16)

# Email configuration
# app.config['MAIL_SERVER'] = 'smtp.yourmailserver.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'your-email@example.com'
# app.config['MAIL_PASSWORD'] = 'your-email-password'
# mail = Mail(app)


print("==================================== APP LETS ====================================")
print("==================================== APP GOGO ======================================")
print("Flask App Secret Key: ", str(secret))

app.config.update({
    'SECRET_KEY': secret,
    'TESTING': True,
    'DEBUG': True
})


#app = Blueprint('app', __name__, template_folder='templates')

from Web_app.subscription import subscription
from Web_app.data_ingestion import data_ingestion
from Web_app.view_history import view_history
from Web_app.decoratorApp import decoratorCheckAppOrg
from Web_app.profile import profile
from Web_app.contact import contact

app.register_blueprint(subscription)
app.register_blueprint(data_ingestion)
app.register_blueprint(view_history)
app.register_blueprint(profile)
app.register_blueprint(contact)

#User session management setup
login_manager = LoginManager()
login_manager.init_app(app)




# Initialize or update the database schema
db_path = "./sqlite_data/sqlite_db"
if not os.path.exists(db_path):
    # If the database does not exist, create it
    with app.app_context():
        init_db_command()
else:
    # Check for schema updates if the database exists
    with app.app_context():
        User.delete_all_subscriptions()
        #drop_table("subscriptions")
        #update_db_schema_command()
        update_db_schema_command()

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
        current_app.logger.debug("Current user is authenticated===============================")
        current_app.logger.debug('This is a debug message')
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
    r_code = response.status_code
    if r_code != 200 and r_code != 302:
       flash('Keycloak is not responding. Status code: ' + str(response.status_code) + ' Try again later!', 'error')
       return render_template('index.html')
    user_name = response.json()["preferred_username"]
    user_email = response.json()["email"]
    unique_id = response.json()["sub"]
    user = User(
    id_=unique_id, name=user_name, email=user_email, token=token, organization=None, domain_name=None
    )
    # Doesn't exist? Add it to the database.
    if not User.get(unique_id): 
        if User.create(unique_id, user_name, user_email, token, None, None) == -1:
            flash('Username and email must be unique.', 'error')
            return render_template('index.html')
    else:
        User.update_field("id", unique_id, "user", "token", token)
    login_user(user)
    return redirect('/home')

@app.route('/home', endpoint='home')
@decoratorCheckAppOrg
def home():
    return render_template('main.html', name = current_user.name, email = current_user.email, tkn = current_user.token)



@app.route('/about', endpoint='about')
@decoratorCheckAppOrg
def home():
    return render_template('about.html', name = current_user.name, email = current_user.email, tkn = current_user.token)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == "__main__":
    print("==================================== APP ====================================")
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(ssl_context="adhoc", host=ipV4IP, port=5005)
    print("==================================== APP END ====================================")
