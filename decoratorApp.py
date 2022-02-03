from flask_login import (
    current_user
)
from flask import render_template
from user import User

def decoratorCheckAppOrg(func):
    def inner():
        if current_user.is_authenticated and User.get_app(current_user.id)==None:
            return render_template('modal.html' , name = current_user.name, email = current_user.email)
        else:
            return func()
    return inner    