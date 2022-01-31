import requests
from flask import Flask, render_template, request, redirect, url_for , jsonify, flash, Blueprint, current_app
import os
import json
import requests
from user import User
from timedata import get_timestamp
from werkzeug.utils import secure_filename
from flask_login import (
    current_user
)

from user import User

data_ingestion = Blueprint('data_ingestion', __name__, template_folder='templates')

@data_ingestion.route("/upload", methods= ['GET', 'POST'])
def ingest_data():
    token = User.get_token(current_user.id) 

    if current_user.is_authenticated:
        if request.method == 'POST':
            file = request.files['jsonFile']
            text=request.form['description']
            
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
                timestamp = get_timestamp()
                filename = secure_filename(file.filename)
                dfmmetadata = {"type": "username", "value": "admin"}
                for i in range(0, len(json_dict["entities"])):
                    json_dict["entities"][i]["dfm_metadata"] = dfmmetadata
                # save uploaded json or create a new file with the same filename and write contents there
                #file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                with open(os.path.join(current_app.config['UPLOAD_FOLDER'], filename), "w") as f:
                    f.write(str(json_dict))
                flash('File uploaded successfully','success')
                User.insert_in_history(current_user.id, timestamp, filename)
                PostOrion(json_dict)
                return redirect(request.url)    
            else:
                flash('Incorrect file type. Please upload a file with content type application/json.','error')
                return redirect(request.url)    
        else:
            return render_template('upload.html',name = current_user.name, email = current_user.email, tkn = token)
    else:
        flash('You should login first!', 'error')
        return redirect(url_for('index'))

def PostOrion(json_dict):
    url = "http://10.0.18.77:1027/v2/op/update"
    # headerPartner = {} 
    # headerPartner['X-Auth-token'] = User.get_token(current_user.id)
    headersDict = {"Content-Type" : "application/json", "X-Auth-token" : User.get_token(current_user.id)}
    #headersDict.update(headerPartner)
    body = json_dict
    sendRequestToOrion(url, headersDict, body)

def sendRequestToOrion(matchPostURL, headersDict, matchBody):
    try:
        r = requests.post(matchPostURL, headers = headersDict, data=json.dumps(matchBody))
        if r.status_code == 204:
            flash('Data sent to orion successfully','success')
        #elif r.status_code == 409:
        #    flash('Device has already been registered','info')
        else:
            flash('Something went wrong','error')
    except requests.exceptions.RequestException as e: 
        flash('Internal error')
        raise SystemExit(e)

