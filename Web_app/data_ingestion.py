import requests
import subprocess
from flask import render_template, request, redirect, flash, Blueprint, current_app
import os
import json
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from user import User
from .timedata import get_timestamp
from werkzeug.utils import secure_filename
from flask_login import (
    current_user
)

# Update with your Elasticsearch URL
ELASTICSEARCH_URL = "http://elasticsearch:9200"
INDEX_NAME = "test_index"  # Update with the name of your Elasticsearch index

data_ingestion = Blueprint('data_ingestion', __name__, template_folder='../templates')

from .decoratorApp import decoratorCheckAppOrg

@data_ingestion.route("/upload", methods= ['GET', 'POST'])
@decoratorCheckAppOrg
def ingest_data():
    current_app.logger.debug("In ingest_data===============================")
    if current_user.is_authenticated:
        if request.method == 'POST':
            file = request.files['jsonFile']
            text = request.form['description']
            if file.filename == '':
                flash('No file was selected', 'error')
                return redirect(request.url)
            if file and (file.content_type == "application/json" or file.content_type == "text/plain"):
                fileContents = file.read()
                try:
                    json_dict = json.loads(fileContents)
                except:
                    flash('Incorrect file type. Please upload a valid json file.', 'error')
                    return redirect(request.url)
                timestamp = get_timestamp()
                filename = secure_filename(file.filename)
                current_app.logger.debug("Sending data to Elasticsearch===============================")
                PostToElasticsearch(json_dict, timestamp, filename, text)
                return redirect(request.url)
            else:
                flash('Incorrect file type. Please upload a file with content type application/json.', 'error')
                return redirect(request.url)
        else:
            token = User.get_field("id", current_user.id, "user", "token")
            return render_template('upload.html', name=current_user.name, email=current_user.email, tkn=token)
    else:
        flash('You should login first!', 'error')
        return redirect("/")

def PostToElasticsearch(json_dict, timestamp, filename, text):
    # Elasticsearch URL and INDEX_NAME should be defined
    url = f"{ELASTICSEARCH_URL.rstrip('/')}/{INDEX_NAME}/_doc/"
    headersDict = {"Content-Type": "application/json"}
    
    # Convert the Python dictionary to a JSON string for the curl command
    json_data = json.dumps(json_dict)
    
    # Prepare the curl command
    #curl_cmd = f"curl -X POST '{url}' -H 'Content-Type: application/json' -d'{json_data}'"
    
    try:
        # Log the curl command
        #current_app.logger.debug(f"Executing curl command: {curl_cmd}")
        
        # Execute the curl command
        #subprocess.run(curl_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Perform the request using the requests library
        response = requests.post(url, headers=headersDict, json=json_dict, timeout=30)
        current_app.logger.debug(f"Response from Elasticsearch: {response.text}")
        
        if response.status_code in [200, 201]:
            flash('File uploaded and indexed successfully', 'success')
            User.insert_in_history(current_user.id, timestamp, filename, text)
        else:
            flash(f'Failed to index document: {response.text}', 'error')
    #except subprocess.CalledProcessError as e:
    #    current_app.logger.error(f"Error executing curl command: {e}")
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error posting to Elasticsearch: {e}")
        flash('Internal error')
