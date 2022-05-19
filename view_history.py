from sqlite3 import Timestamp
import pandas
from flask import Flask, render_template, request, redirect, url_for , jsonify, flash, Blueprint, current_app
from user import User
from flask_login import (
    current_user
)

view_history = Blueprint('view_history', __name__, template_folder='templates')

from decoratorApp import decoratorCheckAppOrg

@view_history.route("/user_history", methods= ['GET', 'POST'])
@decoratorCheckAppOrg
def view_upload_history():
    if current_user.is_authenticated:
        token = User.get_field(current_user.id, "user", "token") 
        if request.method=='GET':
            df = User.fetch_history_dataframe(current_user.id)
            if df.empty:
                message = "You have not uploaded any files yet."
                return render_template("user_history.html", name=current_user.name, data=message)
            df = df.sort_values("timestamp", 0, False)   
            return render_template("user_history.html", name=current_user.name, data=df.to_html(),email = current_user.email, tkn = token)
    else:
        flash('You should login first!', 'error')
        return redirect('/')