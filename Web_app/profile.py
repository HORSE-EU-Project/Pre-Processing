import requests
from flask import render_template, request, redirect, flash, Blueprint, current_app
import os
import json
import requests
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from user import User
from .timedata import get_timestamp
from werkzeug.utils import secure_filename
from flask_login import (
    current_user
)

profile = Blueprint('profile', __name__, template_folder='../templates')

from .decoratorApp import decoratorCheckAppOrg


@profile.route("/profile", methods= ['GET', 'POST'])
@decoratorCheckAppOrg
def edit_profile():
    if current_user.is_authenticated:
        token = User.get_field("id", current_user.id, "user", "token") 
        
        print(current_user.organization)
        if request.method == 'POST':

            if request.form.get('Cancel') == 'Cancel':
                print("cancel time")
                        
                return render_template("main.html", name=current_user.name,email = current_user.email, tkn = token)

            if request.form.get('Save') == 'Save':

                new_url=request.form.get("domain_name")
                new_app=request.form.get("application")
                new_org=request.form.get("organization")

                print("----------->",new_url,new_app,new_org)

                return render_template("main.html", name=current_user.name,email = current_user.email, tkn = token)

        return render_template("profile.html", name=current_user.name,email = current_user.email,application = current_user.application,organization = current_user.organization,domain_name = current_user.domain_name, tkn = token)
    else:
        flash('You should login first!', 'error')
        return redirect('/')