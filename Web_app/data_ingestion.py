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

data_ingestion = Blueprint('data_ingestion', __name__, template_folder='../templates')

from .decoratorApp import decoratorCheckAppOrg

@data_ingestion.route("/upload", methods= ['GET', 'POST'])
@decoratorCheckAppOrg
def ingest_data():
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
                with open(os.path.join("static/json", filename), "w") as f:
                    f.write(str(json_dict))
                PostOrion(json_dict, timestamp, filename, text)
                return redirect(request.url)    
            else:
                flash('Incorrect file type. Please upload a file with content type application/json.','error')
                return redirect(request.url)    
        else:
            token = User.get_field("id", current_user.id, "user", "token")
            return render_template('upload.html',name = current_user.name, email = current_user.email, tkn = token)
    else:
        flash('You should login first!', 'error')
        return redirect("/")

def PostOrion(json_dict, timestamp, filename, text):
    url = "http://10.0.20.174:1027/v2/op/update"
    headersDict = {"Content-Type" : "application/json", "X-Auth-token" : str(User.get_field("id", current_user.id, "user", "token"))}
    body = json_dict
    sendRequestToOrion(url, headersDict, body, timestamp, filename, text)
    return

def sendRequestToOrion(matchPostURL,headersDict,matchBody, timestamp, filename, text):
    try:
        r = requests.post(matchPostURL,headers = headersDict,data= json.dumps(matchBody))
        if r.status_code == 204:
            flash('File uploaded and stored successfully','success')
            User.insert_in_history(current_user.id, timestamp, filename, text)
        else:
            flash('While trying to store the uploaded data en error occurred','error')
    except requests.exceptions.RequestException as e: 
        flash('Internal error')
        raise SystemExit(e)