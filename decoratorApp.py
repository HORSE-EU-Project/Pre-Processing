from flask_login import (
    current_user
)
from flask import render_template
from user import User

def decoratorCheckAppOrg(func):
    def inner():
        if not current_user.is_authenticated:
            view = func()
        elif User.get_app(current_user.id)==None:
            return render_template('modal.html' , name = current_user.name, email = current_user.email)
        else:
            view = func()
        return view
    return inner