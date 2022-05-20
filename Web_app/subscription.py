from flask import render_template, request, redirect, flash, Blueprint
import requests
import json
from flask_login import (
    current_user
)
import sys
import os

from .decoratorApp import decoratorCheckAppOrg

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from user import User

subscription = Blueprint('subscription', __name__, template_folder='../templates')

@subscription.route('/subscribe', methods=['GET', 'POST'])
@decoratorCheckAppOrg
def subscriptionSubmission():
    token = User.get_field("id", current_user.id, "user", "token")
    if current_user.is_authenticated:
        list_apps= User.fetch_applications()
        if request.method == 'POST':
            for i in range(0,len(list_apps)):
                temp_id="id_"+str(list_apps[i])
                temp_url="url_"+str(list_apps[i])
                if request.form.get(temp_id)=="1":
                    createRequest(list_apps[i],request.form.get(temp_url))
            return render_template('subscription.html', name = current_user.name, email = current_user.email, tkn = token,ids=list_apps)
        else :
            return render_template('subscription.html', name = current_user.name, email = current_user.email, tkn = token,ids=list_apps)
    else:
        flash('You should login first!', 'error')
        return redirect("/")

def createRequest(dbName, endpoint):
    url = "http://10.0.20.174:1027/v2/subscriptions/"
    headersDict = {"Content-Type" : "application/json", "X-Auth-token" : User.get_field("id", current_user.id, "user", "token")}
    payload = dict( description = dbName,
                    subject = {"entities" : [], "condition" : {"attrs" : []}},
                    notification = {"http" : {"url": ""}, "attrs" : [], "metadata" : ["dateCreated", "dateModified"]}                
                     )
    payload["subject"]["entities"] = [{"idPattern": ".*","type":dbName}]
    payload["notification"]["http"]["url"] = endpoint
    sendRequestToFiware(url, headersDict, payload)

#Sending a request to fiware       
def sendRequestToFiware(matchPostURL,headersDict,matchPayload):
    try:
        print(matchPostURL)
        print(headersDict)
        print(json.dumps(matchPayload))
        r = requests.post(matchPostURL, headers = headersDict, data= json.dumps(matchPayload))
        print(r.status_code)
        if r.status_code == 201:
            flash('Subscription completed successfully','success')
        #elif r.status_code == 409:
        #    flash('Device has already been registered','info')
        else:
            flash('Something went wrong','error')
    except requests.exceptions.RequestException as e: 
        flash('Internal error')
        raise SystemExit(e)
    