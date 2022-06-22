from flask import render_template, request, redirect, flash, Blueprint
import os
import re
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from user import User
from flask_login import (
    current_user
)

profile = Blueprint('profile', __name__, template_folder='../templates')

from .decoratorApp import decoratorCheckAppOrg
from .subscription import createRequest

@profile.route("/profile", methods= ['GET', 'POST'])
@decoratorCheckAppOrg
def edit_profile():
    if current_user.is_authenticated:
        token = User.get_field("id", current_user.id, "user", "token") 
        old_app_list = User.get_all_cond("apps", "name", "user", current_user.id)
        if request.method == 'POST':
            if request.form.get('Cancel') == 'Cancel':   
                return render_template("main.html", name=current_user.name,email = current_user.email, tkn = token)
            if request.form.get('Save') == 'Save':
                all_apps = User.get_all("apps", "name")
                new_url=request.form.get("domain_name")
                new_org=request.form.get("organization")
                new_app_list = []
                i=1
                appl = request.form.get("app"+str(i))
                while appl!=None:
                    if re.match("^[a-zA-Z0-9_]+$", appl):
                        if appl not in new_app_list:
                            new_app_list.append(appl)
                    else:
                        message = "Application name not allowed. You can use the following characters: [a-z], [A-Z], [0-9] and _"
                        return render_template('profile.html',name=current_user.name,email = current_user.email,old_app_list=old_app_list, old_app_list_len=len(old_app_list), organization = current_user.organization,domain_name = current_user.domain_name, tkn = token, message=message)
                    i += 1
                    appl = request.form.get("app"+str(i))
                temp_list=[]
                for app in old_app_list:
                    if app not in new_app_list:
                        User.delete_app_user(current_user.id, app)
                    else:
                        temp_list.append(app)
                for app in new_app_list:
                    if app not in temp_list:
                        if app not in all_apps:
                            createRequest(appl, "http://quantumleap:8668/v2/notify")
                        User.create_user_app(app, current_user.id)

                User.update_field("id", current_user.id, "user", "domain_name", new_url)
                User.update_field("id", current_user.id, "user", "organization", new_org)

                current_user.organization = new_org
                current_user.domain_name = new_url

                return render_template("profile.html", name=current_user.name,email = current_user.email,old_app_list=new_app_list,old_app_list_len=len(new_app_list),organization = current_user.organization,domain_name = current_user.domain_name, tkn = token)

        return render_template("profile.html", name=current_user.name,email = current_user.email,old_app_list=old_app_list,old_app_list_len=len(old_app_list),organization = current_user.organization,domain_name = current_user.domain_name, tkn = token)
    else:
        flash('You should login first!', 'error')
        return redirect('/')