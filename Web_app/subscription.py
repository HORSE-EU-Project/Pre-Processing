from flask import render_template, request, redirect, flash, Blueprint, current_app
import requests
from urllib.parse import urlparse
import json
from flask_login import (
    current_user
)
import sys
import os
import yaml

from .decoratorApp import decoratorCheckAppOrg

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from user import User


ELASTICSEARCH_URL = "http://elasticsearch:9200"  # Adjust as necessary
INDEX_NAME = "test_index"  # Update with the name of your Elasticsearch index

#set ElastAlert rules directory
ELASTALERT_RULES_DIRECTORY = os.path.join(os.getcwd(), "elastalert/rules")


#create folder if it does not exist
if not os.path.exists(ELASTALERT_RULES_DIRECTORY):
    os.makedirs(ELASTALERT_RULES_DIRECTORY)


# Set the ElastAlert rules directory to be relative to the current working directory
ELASTALERT_RULES_DIRECTORY = os.path.join(os.getcwd(), "elastalert/rules")

subscription = Blueprint('subscription', __name__, template_folder='../templates')

@subscription.route('/subscribe', methods=['GET', 'POST'])
@decoratorCheckAppOrg
def subscriptionSubmission():
    current_app.logger.debug("In subscriptionSubmission===============================")
    token = User.get_field("id", current_user.id, "user", "token")
    if current_user.is_authenticated:
        list_apps= User.get_all("apps", "name")
        if request.method == 'POST':
            for i in range(0,len(list_apps)):
                temp_id="id_"+str(list_apps[i])
                temp_url="url_"+str(list_apps[i])
                if request.form.get(temp_id)=="1":
                    current_app.logger.debug("Calling createElasticsearchWatch===============================")
                    createAlert(list_apps[i],request.form.get(temp_url), INDEX_NAME)
            return render_template('subscription.html', name = current_user.name, email = current_user.email, tkn = token,ids=list_apps)
        else :
            return render_template('subscription.html', name = current_user.name, email = current_user.email, tkn = token,ids=list_apps)
    else:
        flash('You should login first!', 'error')
        return redirect("/")

import json

def createAlert(entity_type, webhook_url, index_name):

    # URL to access the Elasticsearch index
    url = f"{ELASTICSEARCH_URL.rstrip('/')}/{index_name}/_search"

    # Header for HTTP requests
    headersDict = {"Content-Type": "application/json"}

    # Define the query to read the whole database
    query = {
        "query": {
            "match_all": {}
        }
    }

    # Define the rule to be added
    rule = {
        "entity_type": entity_type,
        "es_url": url,
        "query": query,
        "endpoint": webhook_url,
        "headers": headersDict
    }

    # Path to the configuration file
    config_file_path = './ES_alert_system/config.json'

    # Read the existing configuration
    try:
        with open(config_file_path, 'r') as file:
            config_data = json.load(file)
            
    except (FileNotFoundError, json.JSONDecodeError) as e:
        config_data = {}
        current_app.logger.error("Could not open or parse the Alerts file: " + str(e))
        flash("Could not open or parse the Alerts file", 'error')
        # Optionally, create a new file or repair the existing file
        with open(config_file_path, 'w') as file:
            json.dump({"rules": []}, file, indent=4)  # Create a new file with empty rules

    # Append the new rule
    if 'rules' not in config_data:
        config_data['rules'] = []
    config_data['rules'].append(rule)

    # Save the updated configuration back to the file
    try:
        with open(config_file_path, 'w') as file:
            json.dump(config_data, file, indent=4)
            current_app.logger.debug("Alert added successfully to the rules file.")
            flash("Alert added successfully to the rules file", 'success')
    except Exception as e:
        current_app.logger.error("Failed to write to the Alerts file: " + str(e))
        flash("Failed to write to the Alerts file", 'error')
















def sendAlert(entity_type, webhook_url, index_name):
    # Elasticsearch URL and INDEX_NAME should be defined
    url = f"{ELASTICSEARCH_URL.rstrip('/')}/{index_name}/_doc/"
    headersDict = {"Content-Type": "application/json"}
    
    # The query payload is now dynamic with the entity_type
    data = {
        "query": {
            "match": {
                "actionType": entity_type  # Dynamically using entity_type
            }
        },
        "size": 0,  # We only need the count of documents
        "aggs": {
            "count": {"value_count": {"field": "actionType"}}
        }
    }

    try:
        # Making a GET request to Elasticsearch
        response = requests.post(url, headers=headersDict, data=json.dumps(data))

        # Check if the Elasticsearch query was successful
        if response.status_code in [200, 201]:
            count = response.json().get('aggregations', {}).get('count', {}).get('value', 0)
            # Preparing the data to send to the webhook, wrapped in 'data' key
            alert_data = {
                "data": {
                    "message": f"Total documents with 'actionType': '{entity_type}': {count}"
                }
            }
            # Sending a PUT request to the webhook URL
            webhook_response = requests.post(webhook_url, headers=headersDict, data=json.dumps(alert_data))
            if webhook_response.status_code == 200:
                current_app.logger.error("Alert sent successfully to the webhook.")
                flash("Alert sent successfully to the webhook.")
            else:
                current_app.logger.error(f"Failed to send alert to the webhook: {webhook_response.status_code} - {webhook_response.text}")
                flash(f"Failed to send alert to the webhook: {webhook_response.status_code} - {webhook_response.text}")
        else:
            current_app.logger.error(f"Failed to query Elasticsearch: {response.status_code} - {response.text}")
            flash(f"Failed to query Elasticsearch: {response.status_code} - {response.text}")

    except Exception as e:
        current_app.logger.error(f"An error occurred: {str(e)}")
        flash(f"An error occurred: {str(e)}")


    