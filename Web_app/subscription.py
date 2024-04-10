from flask import render_template, request, redirect, flash, Blueprint, current_app
import requests
import json
from flask_login import (
    current_user
)
import sys
import os

from .decoratorApp import decoratorCheckAppOrg

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from user import User


ELASTICSEARCH_URL = "http://elasticsearch:9200"  # Adjust as necessary
WATCHER_ENDPOINT = "/_watcher/watch/"
INDEX_NAME = "test_index"  # Update with the name of your Elasticsearch index


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
                    createElasticsearchWatch(list_apps[i],request.form.get(temp_url))
            return render_template('subscription.html', name = current_user.name, email = current_user.email, tkn = token,ids=list_apps)
        else :
            return render_template('subscription.html', name = current_user.name, email = current_user.email, tkn = token,ids=list_apps)
    else:
        flash('You should login first!', 'error')
        return redirect("/")



def createElasticsearchWatch(Entity_type, endpoint, dbName=INDEX_NAME):
    url = ELASTICSEARCH_URL + WATCHER_ENDPOINT + dbName + "_watch"
    headersDict = {
        "Content-Type": "application/json",
        "Authorization": "Basic <YourEncodedCredentials>"  # Use appropriate auth
    }
    
    # Parse the endpoint URL to extract host, port, and path
    parsed_endpoint = urlparse(endpoint)
    host = parsed_endpoint.hostname
    port = parsed_endpoint.port
    path = parsed_endpoint.path
    
    if not port:  # Default to port 80 if not specified in the URL
        port = 80
        
        
        
    # Example payload - Adjust according to your needs
    payload = {
        "trigger": {
            "schedule": {"interval": "5s"}  # Check every 10 seconds
        },
        "input": {
            "search": {
                "request": {
                    "indices": [dbName],  # Assuming dbName is the index name
                    "body": {
                        "query": {
                            "bool": {
                                "must": [{"match": {"type": Entity_type}}]  # Adjust query
                            }
                        }
                    }
                }
            }
        },
        "condition": {
            "compare": {"ctx.payload.hits.total": {"gt": 0}}  # Condition met when new docs found
        },
        "actions": {
            "notify_endpoint": {
                "webhook": {
                    "method": "POST",
                    "host": host,  # Extract host from 'endpoint'
                    "port": port,  # Adjust as necessary
                    "path": path,  # Extract path from 'endpoint'
                    "headers": {"Content-Type": "application/json"},
                    "body": "{{#toJson}}ctx.payload{{/toJson}}"  # Send payload to endpoint
                }
            }
        }
    }
    # Replace with the actual logic to extract host and path from 'endpoint'
    # And update 'notify_endpoint' in the payload accordingly
    current_app.logger.debug("Sending req to ES===============================")
    sendRequestToElasticsearch(url, headersDict, payload)

# Adjusted function to send request to Elasticsearch
def sendRequestToElasticsearch(matchPostURL, headersDict, matchPayload):
    try:
        r = requests.put(matchPostURL, headers=headersDict, data=json.dumps(matchPayload))
        if r.status_code in [200, 201]:
            flash('Watcher created successfully', 'success')
        else:
            flash(f'Something went wrong: {r.text}', 'error')
    except requests.exceptions.RequestException as e:
        flash('Internal error')
        raise SystemExit(e)






def createRequest(dbName, endpoint):
    url = ORION_URL+"/v2/subscriptions/"
    headersDict = {"Content-Type" : "application/json"}
    payload = dict( description = dbName,
                    subject = {"entities" : [], "condition" : {"attrs" : []}},
                    notification = {"http" : {"url": ""}, "attrs" : [], "metadata" : ["dateCreated", "dateModified"]}                
                    )
    payload["subject"]["entities"] = [{"idPattern": ".*","type":dbName}]
    payload["notification"]["http"]["url"] = endpoint
    sendRequestToFiware(url, headersDict, payload)

#Sending a request to fiware       
def sendRequestToFiware(matchPostURL,headersDict,matchPayload):
    try:
        r = requests.post(matchPostURL, headers = headersDict, data= json.dumps(matchPayload))
        if r.status_code == 201:
            flash('Subscription created successfully','success')
        #elif r.status_code == 409:
        #    flash('Device has already been registered','info')
        else:
            flash('Something went wrong','error')
    except requests.exceptions.RequestException as e: 
        flash('Internal error')
        raise SystemExit(e)
    