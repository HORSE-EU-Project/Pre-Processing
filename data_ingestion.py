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
                timestamp = get_timestamp()
                print(timestamp)
                filename = secure_filename(file.filename)
                '''
                "metadata": {
	                "username": "stelio",
	                "dateUploaded": "2022-01-12T11:17:24.115+00:00"
	            }
                '''
                metadata = {"username": current_user.name, "dateUploaded": str(timestamp)}
                json_dict["metadata"] = metadata
                # save uploaded json or create a new file with the same filename and write contents there
                #file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                with open(os.path.join(current_app.config['UPLOAD_FOLDER'], filename), "w") as f:
                    f.write(str(json_dict))
                flash('File uploaded successfully','success')
                User.insert_in_history(current_user.id, timestamp, filename)
                print(User.get_history(current_user.id))
                PostOrion(json_dict)
                return redirect(request.url)    
            else:
                flash('Incorrect file type. Please upload a file with content type application/json.','error')
                return redirect(request.url)    
        else:
            return render_template('upload.html',name = current_user.name, email = current_user.email)
    else:
        flash('You should login first!', 'error')
        return redirect(url_for('index'))

def PostOrion(json_dict):
    url = "http://10.0.18.77:1027/v2/op/update"
    

    headersDict = {"Content-Type" : "application/json", "X-Auth-token" : str(User.get_token(current_user.id))}

    body = json_dict
    print(body)
    sendRequestToOrion(url, headersDict,body)

def sendRequestToOrion(matchPostURL,headersDict,matchBody):
    try:
        r = requests.post(matchPostURL,headers = headersDict,data= matchBody)
        print("----------",r.status_code)
        if r.status_code == 204:
            flash('Subscription completed successfully','success')
        #elif r.status_code == 409:
        #    flash('Device has already been registered','info')
        else:
            flash('Something went wrong','error')
    except requests.exceptions.RequestException as e: 
        flash('Internal error')
        raise SystemExit(e)

