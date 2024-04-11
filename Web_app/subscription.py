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

ELASTALERT_RULES_DIRECTORY = "/etc/elastalert/rules"  # Adjust as necessary

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
                    createAlert(list_apps[i],request.form.get(temp_url))
            return render_template('subscription.html', name = current_user.name, email = current_user.email, tkn = token,ids=list_apps)
        else :
            return render_template('subscription.html', name = current_user.name, email = current_user.email, tkn = token,ids=list_apps)
    else:
        flash('You should login first!', 'error')
        return redirect("/")



def createAlert(index_name, webhook_url):
    # Define the rule name based on the index name
    rule_name = f"{index_name}_alert_rule.yaml"

    # Path to the rule file
    rule_file_path = os.path.join(ELASTALERT_RULES_DIRECTORY, rule_name)

    # Define the rule configuration
    rule_config = {
        "name": f"Alert for {index_name}",
        "type": "any",
        "index": index_name,
        "alert": "webhook",
        "alert_text_type": "alert_text_only",
        "alert_subject": f"Change detected in {index_name}",
        "alert_text": "Change detected at @timestamp. Document: @doc.",
        "webhook": {
            "http_post_url": webhook_url,
        }
    }
    
    # Write the rule configuration to the rule file with error handling
    try:
        with open(rule_file_path, "w") as rule_file:
            yaml.dump(rule_config, rule_file)
    except Exception as e:
        current_app.logger.error(f"Error writing rule configuration to file: {e}")
        return
    