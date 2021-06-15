
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

@subscription.route('/consumer', methods=['GET', 'POST'])
def showHtml():
    if request.method == 'POST':
        if request.form.get('fr'):
            dbname = 'FrSensorsPlatform'
            createRequest(dbname,request.form.get('url-fr'))
            #ALEX make request to FR
            #check request response -  produce flash messages to demonstrate success or fail in consumer.html
        if request.form.get('xb'):
            dbname = 'XBELLO'
            createRequest(dbname,request.form.get('url-xb'))
            #ALEX make request to XBello
        if request.form.get('tr'):
            dbname = 'Triage Platform'
            createRequest(dbname,request.form.get('url-tr'))
            #ALEX make request to TRiage
        if request.form.get('ai'):
            dbname = 'AirflowMCC'
            createRequest(dbname,request.form.get('url-ai'))
            #ALEX make request to Air
        if request.form.get('si'):
            dbname = 'Sivi'
            createRequest(dbname,request.form.get('url-si'))
            #print(urlsi)
            #ALEX make request to Sivi
        return render_template('subscription.html')
    else :
        return render_template('subscription.html')

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



def subscribe():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return render_template('subscription.html')
        else:
            flash('You should login first!', 'error')
            return redirect(url_for('index'))
    else:
        #print(request.form.get('fr'))
        if request.form.get('fr'):
            urlfr = request.form.get('url-fr')
            #print(urlfr)
            #ALEX make request to FR
            #check request response -  produce flash messages to demonstrate success or fail in consumer.html
        if request.form.get('xb'):
            urlxb = request.form.get('url-xb')
            #ALEX make request to XBello
        if request.form.get('tr'):
            urltr = request.form.get('url-tr')
            #ALEX make request to TRiage
        if request.form.get('ai'):
            urlai = request.form.get('url-ai')
            #ALEX make request to Air
        if request.form.get('si'):
            urlsi = request.form.get('url-si')
            print(urlsi)
            #ALEX make request to Sivi
  
        return render_template('consumer.html')
'''
def systems():
#create dictionary of systems available in our DB
    rands = random.sample(range(1, 1000), 5)
    global systems_dict 
    systems_dict = {
        "Fr": rands[0],
        "Xb": rands[1],
        "Tr": rands[2],
        "Ai": rands[3],
        "Si": rands[4]
    }
    for item in systems_dict.items():
        print(item)
    return render_template('subscription.html', **systems_dict)
'''
@subscription.route('/consumer/subscription')
def createSubscription():
    #if request.args.get('system') == 'Fr':
    return render_template('subscription.html')

#Parsing the uploaded registration file
def makeSubscription(filename):
    with open('static/json/' + filename, 'r') as file:
        fileContents = file.read().replace(' ', '')
        #Get url
        httpPattern = r'h.*subscriptions'
        try:
            matchPostURL = re.search(httpPattern, fileContents).group()
            #print(matchPostURL)
        except AttributeError:
            print('Couldn\'t find the url')
            flash('Error getting url','error')
            matchPostURL = re.search(httpPattern, fileContents)
        #Get headers!
        headersPattern = r'(?<=\')[\w:/-]+(?=\')'
        try:
            matchHeaders = re.findall(headersPattern, fileContents)
            #print(matchHeaders)
        except AttributeError:
            print('error Headers')
            flash('Error getting headers','error')
        #Creating dict of headers
        headersDict = {}
        for item in matchHeaders:
            a = item.split(':')
            headersDict[a[0]] = a[1]
        #print(headersDict)
            
        #Returnpayload
        payloadPattern =r'(?<=\')\{[\w\W\s\S\d\D]+\}(?=(\s)*\')'
        try:
            matchPayload = re.search(payloadPattern, fileContents).group()
            #print(matchPayload)
        except AttributeError:
            print('error Payload')
            flash('Error getting correct payload','error') 
        #print(matchPayload)
        sendRequestToFiware(matchPostURL,headersDict,matchPayload)
        
#Sending a request to fiware       
def sendRequestToFiware(matchPostURL,headersDict,matchPayload):
    #print(headersDict)
    try:
        print(matchPostURL)
        print(headersDict)
        print(json.dumps(matchPayload))
        r = requests.post(matchPostURL,headers = headersDict,data= json.dumps(matchPayload))
        if r.status_code == 201:
            flash('Subscription completed successfully','success')
        elif r.status_code == 409:
            flash('Device has already been registered','info')
        #print(r.status_code)
    except requests.exceptions.RequestException as e: 
        flash('Internal error')
        raise SystemExit(e)