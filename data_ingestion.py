import requests
from flask import Flask, render_template, request, redirect, url_for , jsonify, flash, Blueprint, current_app
import os
import json
import requests
from werkzeug.utils import secure_filename
from flask_login import (
    current_user
)

from user import User

data_ingestion = Blueprint('data_ingestion', __name__, template_folder='templates')

@data_ingestion.route("/ingest", methods= ['GET', 'POST'])
def ingest_data():
    if current_user.is_authenticated:
        if request.method == 'POST':
            file = request.files['jsonFile']
            if file.filename == '':
                flash('No file was selected','error')
                return redirect(request.url)
            # ensure that uploaded file is valid json
            if file and (file.content_type=="application/json" or file.content_type=="text/plain"):
                fileContents = file.read()
                try:    
                    json_dict=json.loads(fileContents)
                except:
                    flash('Incorrect file type. Please upload a valid json file.','error')
                    return redirect(request.url)  
                print(fileContents)
                filename = secure_filename(file.filename)
                # save uploaded json or create a new file with the same filename and write contents there
                #file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                with open(os.path.join(current_app.config['UPLOAD_FOLDER'], filename), "w") as f:
                    f.write(str(json_dict))
                flash('File uploaded successfully','success')
                PostOrion(json_dict)
                return redirect(request.url)    
            else:
                flash('Incorrect file type. Please upload a file with content type application/json.','error')
                return redirect(request.url)    
        else:
            return render_template('upload.html')
    else:
        flash('You should login first!', 'error')
        return redirect(url_for('index'))

def PostOrion(json_dict):
    url = "http://10.0.18.77:1027/v2/op/update"
    headerPartner = {}
    
    headerPartner['X-Auth-token'] = User.get_token(current_user.id)
    headersDict = {"Content-Type" : "application/json", "X-Auth-token" : "/"}
    headersDict.update(headerPartner)

    body = dict( 
        {   "actionType":"APPEND",
            "entities":[
                {
                    "id":"mobileID001", "type": "geoJson",
                    "timestamp": {"type": "Datetime", "value": "10-04-19 12:00:17"},
                    "LAT": {"type": "latitude", "value": 1111},
                    "LON": {"type": "longitude", "value": "hello"}
                }
            ]
        }
    )
    #payload["subject"]["entities"] = [{"idPattern" : ".*"}]
    #payload["notification"]["http"]["url"] = endpoint
    sendRequestToOrion(url, headersDict,body)

def sendRequestToOrion(matchPostURL,headersDict,matchBody):
    try:
        print("matchPostURL",matchPostURL)
        print("headersDict",headersDict)
        print("-------json",json.dumps(matchBody))
        r = requests.post(matchPostURL,headers = headersDict,data= json.dumps(matchBody))
        if r.status_code == 201:
            flash('Subscription completed successfully','success')
        #elif r.status_code == 409:
        #    flash('Device has already been registered','info')
        else:
            flash('Something went wrong','error')
    except requests.exceptions.RequestException as e: 
        flash('Internal error')
        raise SystemExit(e)
'''
#Parsing the uploaded registration file
def registerDevice(filename):
    with open('static/json/' + filename, 'r') as file:
        fileContents = file.read().replace(' ', '')
        #Get url
        httpPattern = r'h.*devices'
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
        r = requests.post(matchPostURL,headers = headersDict,data= matchPayload)
        if r.status_code == 201:
            flash('Device registered successfully','success')
        elif r.status_code == 409:
            flash('Device has already been registered','info')
        #print(r.status_code)
    except requests.exceptions.RequestException as e: 
        flash('Internal error')
        raise SystemExit(e)
        '''