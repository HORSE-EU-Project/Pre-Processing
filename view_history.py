import pandas
from flask import Flask, render_template, request, redirect, url_for , jsonify, flash, Blueprint, current_app
from user import User
from flask_login import (
    current_user
)

view_history = Blueprint('view_history', __name__, template_folder='templates')

@view_history.route("/main/user_history", methods= ['GET', 'POST'])
def view_upload_history():
    if current_user.is_authenticated:
        if request.method=='GET':
            df = User.fetch_history_dataframe(current_user.id)
            if df.empty:
                message = "You have not uploaded any files yet."
                return render_template("user_history.html", name=current_user.name, data=message)   
            return render_template("user_history.html", name=current_user.name, data=df.to_html())
    else:
        flash('You should login first!', 'error')
        return redirect(url_for('index'))