from logging import exception
from flask import Flask, render_template, request, redirect, url_for , flash, Blueprint
from os.path import join, dirname, realpath
import requests
import json
from flask_login import (
    current_user
)
from user import User
subscription = Blueprint('subscription', __name__, template_folder='templates')


@subscription.route('/subscribe', methods=['GET', 'POST'])
def subscriptionSubmission():
    token = User.get_token(current_user.id) 

    if current_user.is_authenticated:
        if request.method == 'POST':
            if request.form.get('fr'):
                dbname = 'FrSensorsPlatform'
                db_id = 'dataLoggerID'
                createRequest(dbname,request.form.get('url-fr'), db_id)         
                #check request response -  produce flash messages to demonstrate success or fail in consumer.html
            if request.form.get('xb'):
                dbname = 'XBELLO'
                db_id = 'mobileID'
                createRequest(dbname,request.form.get('url-xb'), db_id)
            if request.form.get('tr'):
                dbname = 'Triage_Platform'
                db_id = 'tagID'
                createRequest(dbname,request.form.get('url-tr'), db_id) 
            if request.form.get('ai'):
                dbname = 'AirflowMCC'
                db_id = 'uxvID'
                createRequest(dbname,request.form.get('url-ai'), db_id)         
            if request.form.get('si'):
                dbname = 'Sivi'
                db_id = 'sID'
                createRequest(dbname,request.form.get('url-si'), db_id)
            return render_template('subscription.html', name = current_user.name, email = current_user.email, tkn = token)
        else :
            return render_template('subscription.html', name = current_user.name, email = current_user.email, tkn = token)
    else:
        flash('You should login first!', 'error')
        return redirect(url_for('index'))

def createRequest(dbName, endpoint, db_id):
    url = "http://10.0.18.77:1027/v2/subscriptions/"
    headersDict = {"Content-Type" : "application/json", "X-Auth-token" : User.get_token(current_user.id)}
    #constructing payload
    #entities = [{"idPattern" : ".*"}]
    #condition = {"attrs" : []}
    payload = dict( description = dbName,
                    subject = {"entities" : [], "condition" : {"attrs" : []}},
                    notification = {"http" : {"url": ""}, "attrs" : [], "metadata" : ["dateCreated", "dateModified"]}                
                     )
    payload["subject"]["entities"] = [{"idPattern" : db_id + ".*"}]
    payload["notification"]["http"]["url"] = endpoint
    sendRequestToFiware(url, headersDict, payload)


#Sending a request to fiware       
def sendRequestToFiware(matchPostURL,headersDict,matchPayload):
    try:
        print(matchPostURL)
        print(headersDict)
        print(json.dumps(matchPayload))
        r = requests.post(matchPostURL, headers = headersDict, data= json.dumps(matchPayload))
        if r.status_code == 201:
            flash('Subscription completed successfully','success')
        #elif r.status_code == 409:
        #    flash('Device has already been registered','info')
        else:
            flash('Something went wrong','error')
    except requests.exceptions.RequestException as e: 
        flash('Internal error')
        raise SystemExit(e)
    