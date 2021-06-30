
from io import StringIO
import random
from logging import exception
from flask import Flask, render_template, request, redirect, url_for , jsonify, flash, Blueprint, current_app
import os
from os.path import join, dirname, realpath
#from requests.api import head
#from requests.models import HTTPError
from werkzeug.datastructures import Headers
from werkzeug.utils import secure_filename
import socket
#import fi
import re
import requests
import json
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
    UserMixin
)

subscription = Blueprint('subscription', __name__, template_folder='templates')


@subscription.route('/subscribe', methods=['GET', 'POST'])
def subscriptionSubmission():
    if request.method == 'POST':
        if request.form.get('fr'):
            dbname = 'FrSensorsPlatform'
            createRequest(dbname,request.form.get('url-fr'))         
            #check request response -  produce flash messages to demonstrate success or fail in consumer.html
        if request.form.get('xb'):
            dbname = 'XBELLO'
            createRequest(dbname,request.form.get('url-xb'))
        if request.form.get('tr'):
            dbname = 'Triage_Platform'
            createRequest(dbname,request.form.get('url-tr')) 
        if request.form.get('ai'):
            dbname = 'AirflowMCC'
            createRequest(dbname,request.form.get('url-ai'))         
        if request.form.get('si'):
            dbname = 'Sivi'
            createRequest(dbname,request.form.get('url-si'))
        return render_template('subscription.html')
    else :
        if current_user.is_authenticated:
            return render_template('subscription.html')
        else:
            flash('You should login first!', 'error')
            return redirect(url_for('index'))

def createRequest(dbName, endpoint):
    url = "http://10.0.20.226:1026/v2/subscriptions/"
    headerPartner = {}
    headerPartner['Fiware-Service'] = dbName
    headersDict = {"Content-Type" : "application/json", "Fiware-ServicePath" : "/"}
    headersDict.update(headerPartner)
    #constructing payload
    #entities = [{"idPattern" : ".*"}]
    #condition = {"attrs" : []}
    payload = dict( description = dbName,
                    subject = {"entities" : [], "condition" : {"attrs" : []}},
                    notification = {"http" : {"url": ""}, "attrs" : [], "metadata" : ["dateCreated", "dateModified"]}                
                     )
    payload["subject"]["entities"] = [{"idPattern" : ".*"}]
    payload["notification"]["http"]["url"] = endpoint
    sendRequestToFiware(url, headersDict,payload)


#Sending a request to fiware       
def sendRequestToFiware(matchPostURL,headersDict,matchPayload):
    #print(headersDict)
    try:
        print(matchPostURL)
        print(headersDict)
        print(json.dumps(matchPayload))
        r = requests.post(matchPostURL,headers = headersDict,data= json.dumps(matchPayload))
        #print(r.status_code)
        if r.status_code == 201:
            flash('Subscription completed successfully','success')
<<<<<<< HEAD
        elif r.status_code == 409:
            flash('Device has already been registered','info')
        else:
            flash('Something went wrong','error')
            print(r.status_code)
=======
        #elif r.status_code == 409:
        else:
            flash('Subscription has not been established correctly','info')
>>>>>>> 8f4d953abb60534f428d65c134fe56fafdb431aa
    except requests.exceptions.RequestException as e: 
        flash('Internal error')
        raise SystemExit(e)