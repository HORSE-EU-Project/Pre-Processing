from flask_login import (
    current_user
)
from flask import render_template
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from user import User

def decoratorCheckAppOrg(func):
    def inner():
        # if current_user.is_authenticated and (User.get_field("user_id", current_user.id, "apps", "name")==-1 or User.get_field("id", current_user.id, "user", "organization")==None):
        #     return render_template('modal.html' , name = current_user.name, email = current_user.email)
        # else:
        return func()
    return inner    