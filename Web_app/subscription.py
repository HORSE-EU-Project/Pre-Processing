from flask import render_template, request, redirect, url_for, flash, Blueprint, current_app
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


ELASTICSEARCH_URL = "http://10.10.10.14:9200"  # Adjust as necessary
INDEX_NAME = "test_index"  # Update with the name of your Elasticsearch index

subscription = Blueprint('subscription', __name__, template_folder='../templates')

@subscription.route('/subscribe', methods=['GET', 'POST'], endpoint='view_subscriptions')
@decoratorCheckAppOrg
def subscriptionSubmission():
    current_app.logger.debug("In subscriptionSubmission view")
    if not current_user.is_authenticated:
        flash('You must log in first!', 'error')
        return redirect("/")

    token = User.get_field("id", current_user.id, "user", "token")
    all_subscriptions = User.get_subscriptions(current_user.id)  # Use the static method to get all subscriptions

    # Pagination logic
    page = request.args.get('page', 1, type=int)  # Get the page number from query parameter
    items_per_page = 10
    total_pages = (len(all_subscriptions) + items_per_page - 1) // items_per_page  # Calculate total pages
    start = (page - 1) * items_per_page
    end = start + items_per_page
    subscriptions = all_subscriptions[start:end]  # Slice the subscriptions for the current page

    if request.method == 'POST':
        list_apps = User.get_all("apps", "name")
        action = request.form.get('action')
        if action == 'sync':
            # Update the subscription on the yaml file based on the SQLite database
            result = User.sync_subscriptions(current_user.id)
            if result == 'Subscriptions successfully synced to the YAML file.':
                flash("Subscriptions synchronized successfully", 'success')
            else:
                flash("Failed to synchronize subscriptions: " + result, 'error')
            current_app.logger.debug(result)
        
        return redirect(url_for('subscription.view_subscriptions', page=page))  # Redirect to the same page to avoid form resubmission

    return render_template('subscription_view.html', subscriptions=subscriptions, tkn=token, name=current_user.name,
                           email=current_user.email, total_pages=total_pages, current_page=page)



@subscription.route('/subscribe/form', methods=['GET', 'POST'], endpoint='form')
@decoratorCheckAppOrg
def subscription_form():
    current_app.logger.debug("In subscription form")
    if current_user.is_authenticated:
        token = User.get_field("id", current_user.id, "user", "token")
        subscriptions = User.get_subscriptions(current_user.id)  # Use the static method to get subscriptions

        if request.method == 'POST':
            subscription_id = request.form.get('subscription_id')
            # Based on the subscription_id, get the subscription details
            subscription = dict(User.get_subscription(subscription_id))
            
            #print(subscription fields)
            current_app.logger.debug("Subscription fields: " + str(subscription))
            
            
            # Check if subscription data is fetched
            form_data = {
                'form_title': "Edit Subscription",
                'subscription_type': str(subscription['subscription_type']),
                'endpoint_url': str(subscription['endpoint_url']),
                'DB_url': str(subscription['DB_url']),
                'query': str(subscription['query']),
                'interval': str(subscription['interval']),
                'active': bool(subscription['active']),  # This controls whether the checkbox is checked
                'button_text': "Update Subscription",  # Text for the submit button
                'action': 'update',  # Action to be taken when the form is submitted
                'subscription_id': subscription_id # Hidden field to store the subscription ID
            }
            current_app.logger.debug("Subscription found with ID: " + str(subscription_id))
                
            
            #Fill the form with the subscription details
            return render_template('create_subscription.html', subscription=subscription, tkn=token, name=current_user.name, email=current_user.email, **form_data)
            
            #return redirect(url_for('subscription.view_subscriptions'))
        else:
            form_data = {
                'form_title': "Edit Subscription",
                'button_text': "Update Subscription"  # Text for the submit button
            }
            return render_template('create_subscription.html', subscriptions=subscriptions, tkn=token, name=current_user.name, email=current_user.email, **form_data)
    else:
        flash('You must log in first!', 'error')
        return redirect("/")

@subscription.route('/subscribe/new', methods=['GET', 'POST'], endpoint='new')
@decoratorCheckAppOrg
def create_subscription():
    token = User.get_field("id", current_user.id, "user", "token")
    
    if current_user.is_authenticated:
        list_apps= User.get_all("apps", "name")
        if request.method == 'POST':
            # Collect data from form
            action = request.form.get('action')
            subscription_type = request.form.get('subscription_type')
            endpoint_url = request.form.get('endpoint_url')
            DB_url = request.form.get('DB_url')
            query = request.form.get('query')
            interval = request.form.get('interval')
            active = request.form.get('active', 'off') == 'on'
            es_index = None
            entity = None
            if subscription_type == 'ES':
                es_index = request.form.get('index')
            elif subscription_type == 'ORION':
                entity = request.form.get('entity')
            
            if action == 'update':
                # Update the subscription
                subscription_id = request.form.get('subscription_id')
                result = User.update_subscription(
                    subscription_id = subscription_id,
                    user_id=current_user.id,
                    subscription_type=subscription_type,
                    endpoint_url=endpoint_url,
                    DB_url=DB_url,
                    query=query,
                    interval=interval,
                    active=active,
                    es_index=es_index,
                    entity=entity
                )
                if result == 'Subscription updated successfully':
                    flash("Subscription updated successfully.", 'success')
                else:
                    flash("Failed to update subscription: " + result, 'error')
                return redirect(url_for('subscription.view_subscriptions'))
            
            elif action == 'delete':
                # Delete the subscription
                subscription_id = request.form.get('subscription_id')
                result = User.delete_subscription(subscription_id, current_user.id)
                if result == 'Subscription deleted successfully':
                    flash("Subscription deleted successfully.", 'success')
                else:
                    flash("Failed to delete subscription: " + result, 'error')
                return redirect(url_for('subscription.view_subscriptions'))
            
            # Call the User class method to create a subscription
            else:
                result = User.create_subscription(
                    user_id=current_user.id,
                    subscription_type=subscription_type,
                    endpoint_url=endpoint_url,
                    DB_url=DB_url,
                    query=query,
                    interval=interval,
                    active=active
                )

                # Flash message and redirect based on the outcome
                if result == 'Subscription created successfully':
                    current_app.logger.debug("Subscription created successfully.")
                    flash("Subscription created successfully.", 'success')
                    return redirect(url_for('subscription.view_subscriptions'))
                else:
                    current_app.logger.debug("Failed to create subscription"+ result)
                    flash("Failed to create subscription: " + result, 'error')
                    return redirect(url_for('subscription.form'))

            
        else:
            form_data = {
                'form_title': "New Subscription",
                'button_text': "Create Subscription"  # Text for the submit button
            } 
            return render_template('create_subscription.html', tkn=token, name=current_user.name, email=current_user.email, **form_data)
    else:
        flash('You should login first!', 'error')
        return redirect("/")





def createAlert(entity_type, webhook_url, index_name):
    # URL to access the Elasticsearch index
    url = f"{ELASTICSEARCH_URL.rstrip('/')}/{index_name}/_search"

    # Header for HTTP requests
    headersDict = {"Content-Type": "application/json"}

    # Define the query to read the whole database
    query = {
            "match_all": {}
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
        flash("Could not open or parse the Alerts file -- Error: "+ str(e), 'error')
        # return # Exit the function
        return False
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
            return True
    except Exception as e:
        current_app.logger.error("Failed to write to the Alerts file: " + str(e))
        flash("Failed to write to the Alerts file", 'error')
        return False