import requests
import json
import os
import sys
from flask import render_template, request, redirect, flash, Blueprint, current_app
from werkzeug.utils import secure_filename
from flask_login import current_user
from dotenv import load_dotenv
from .timedata import get_timestamp
from user import User
from .decoratorApp import decoratorCheckAppOrg

# Load environment variables from .env file
load_dotenv()

ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://elasticsearch:9200')
INDEX_NAME = os.getenv('INDEX_NAME', 'test_index')

data_ingestion = Blueprint('data_ingestion', __name__, template_folder='../templates')

@data_ingestion.route("/upload", methods=['GET', 'POST'], endpoint='upload')
@decoratorCheckAppOrg
def ingest_data():
    if not current_user.is_authenticated:
        flash('You should login first!', 'error')
        return redirect("/")

    if request.method == 'POST':
        file = request.files.get('jsonFile')
        text = request.form.get('description', '').strip()

        if not file or file.filename == '':
            flash('No file was selected', 'error')
            return redirect(request.url)

        if file and file.content_type in ["application/json", "text/plain"]:
            try:
                file_contents = file.read()
                json_dict = json.loads(file_contents)
            except json.JSONDecodeError:
                flash('Invalid JSON file. Please upload a valid JSON file.', 'error')
                return redirect(request.url)

            timestamp = get_timestamp()
            filename = secure_filename(file.filename)
            current_app.logger.debug("Sending data to Elasticsearch")

            if PostToElasticsearch(json_dict, timestamp, filename, text):
                flash('File uploaded and indexed successfully', 'success')
            else:
                flash('Failed to index document', 'error')
                
            return redirect(request.url)

        else:
            flash('Incorrect file type. Please upload a file with content type application/json.', 'error')
            return redirect(request.url)

    token = User.get_field("id", current_user.id, "user", "token")
    return render_template('upload.html', name=current_user.name, email=current_user.email, tkn=token)

def PostToElasticsearch(json_dict, timestamp, filename, text):
    url = f"{ELASTICSEARCH_URL.rstrip('/')}/{INDEX_NAME}/_doc/"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=json_dict, timeout=30)
        current_app.logger.debug(f"Response from Elasticsearch: {response.text}")

        if response.status_code in [200, 201]:
            User.insert_in_history(current_user.id, timestamp, filename, text)
            return True
        else:
            current_app.logger.error(f"Failed to index document: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error posting to Elasticsearch: {e}")
        return False
