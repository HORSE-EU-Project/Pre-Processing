from flask import render_template, request, redirect, url_for, flash, Blueprint, current_app
import requests
from urllib.parse import urlparse
import json
from flask_login import current_user
import sys
import os
import yaml
import re
from werkzeug.utils import secure_filename

from .decoratorApp import decoratorCheckAppOrg
from user import User

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from user import User

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://elasticsearch:9200')
INDEX_NAME = os.getenv('INDEX_NAME', 'test_index')

subscription = Blueprint('subscription', __name__, template_folder='../templates')

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def is_valid_query(query):
    try:
        json.loads(query)
        return True
    except ValueError:
        return False

def is_valid_subscription_id(subscription_id):
    return bool(re.match(r'^[a-zA-Z0-9_-]{5,50}$', subscription_id))

def sanitize_string(value):
    return re.sub(r'[^\w\s-]', '', value).strip()

@subscription.route('/subscribe', methods=['GET', 'POST'], endpoint='view_subscriptions')
@decoratorCheckAppOrg
def subscriptionSubmission():
    current_app.logger.debug("In subscriptionSubmission view")
    if not current_user.is_authenticated:
        flash('You must log in first!', 'error')
        return redirect("/")

    token = User.get_field("id", current_user.id, "user", "token")
    all_subscriptions = User.get_subscriptions(current_user.id)

    # Pagination logic
    page = request.args.get('page', 1, type=int)
    items_per_page = 10
    total_pages = (len(all_subscriptions) + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    end = start + items_per_page
    subscriptions = all_subscriptions[start:end]

    if request.method == 'POST':
        list_apps = User.get_all("apps", "name")
        action = request.form.get('action')
        if action == 'sync':
            result = User.sync_subscriptions(current_user.id)
            if result == 'Subscriptions successfully synced to the YAML file.':
                flash("Subscriptions synchronized successfully", 'success')
            else:
                flash("Failed to synchronize subscriptions: " + result, 'error')
            current_app.logger.debug(result)
        
        return redirect(url_for('subscription.view_subscriptions', page=page))

    return render_template('subscription_view.html', subscriptions=subscriptions, tkn=token, name=current_user.name,
                           email=current_user.email, total_pages=total_pages, current_page=page)

@subscription.route('/subscribe/form', methods=['GET', 'POST'], endpoint='form')
@decoratorCheckAppOrg
def subscription_form():
    current_app.logger.debug("In subscription form")
    if current_user.is_authenticated:
        token = User.get_field("id", current_user.id, "user", "token")
        subscriptions = User.get_subscriptions(current_user.id)

        if request.method == 'POST':
            subscription_id = request.form.get('subscription_id')
            if not is_valid_subscription_id(subscription_id):
                flash('Invalid subscription ID format', 'error')
                return redirect(url_for('subscription.view_subscriptions'))

            subscription = dict(User.get_subscription(subscription_id))
            current_app.logger.debug("Subscription fields: " + str(subscription))
            
            form_data = {
                'form_title': "Edit Subscription",
                'subscription_type': sanitize_string(str(subscription.get('subscription_type', ''))),
                'endpoint_url': sanitize_string(str(subscription.get('endpoint_url', ''))),
                'DB_url': sanitize_string(str(subscription.get('DB_url', ''))),
                'query': sanitize_string(str(subscription.get('query', ''))),
                'interval': sanitize_string(str(subscription.get('interval', ''))),
                'active': bool(subscription.get('active', False)),
                'button_text': "Update Subscription",
                'action': 'update',
                'subscription_id': subscription_id
            }
            current_app.logger.debug("Subscription found with ID: " + str(subscription_id))
            
            return render_template('create_subscription.html', subscription=subscription, tkn=token, name=current_user.name, email=current_user.email, **form_data)
            
        else:
            form_data = {
                'form_title': "Edit Subscription",
                'button_text': "Update Subscription"
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
        list_apps = User.get_all("apps", "name")
        if request.method == 'POST':
            action = request.form.get('action')
            subscription_type = sanitize_string(request.form.get('subscription_type', ''))
            endpoint_url = request.form.get('endpoint_url')
            DB_url = request.form.get('DB_url')
            query = request.form.get('query')
            interval = request.form.get('interval')
            active = request.form.get('active', 'off') == 'on'
            es_index = sanitize_string(request.form.get('index', ''))
            entity = sanitize_string(request.form.get('entity', ''))
            
            if not is_valid_url(endpoint_url):
                flash('Invalid endpoint URL format', 'error')
                return redirect(url_for('subscription.form'))

            if not is_valid_query(query):
                flash('Invalid query format', 'error')
                return redirect(url_for('subscription.form'))

            if action == 'update':
                subscription_id = request.form.get('subscription_id')
                if not is_valid_subscription_id(subscription_id):
                    flash('Invalid subscription ID format', 'error')
                    return redirect(url_for('subscription.form'))

                result = User.update_subscription(
                    subscription_id=subscription_id,
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
                subscription_id = request.form.get('subscription_id')
                if not is_valid_subscription_id(subscription_id):
                    flash('Invalid subscription ID format', 'error')
                    return redirect(url_for('subscription.view_subscriptions'))

                result = User.delete_subscription(subscription_id, current_user.id)
                if result == 'Subscription deleted successfully':
                    flash("Subscription deleted successfully.", 'success')
                else:
                    flash("Failed to delete subscription: " + result, 'error')
                return redirect(url_for('subscription.view_subscriptions'))
            
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

                if result == 'Subscription created successfully':
                    current_app.logger.debug("Subscription created successfully.")
                    flash("Subscription created successfully.", 'success')
                    return redirect(url_for('subscription.view_subscriptions'))
                else:
                    current_app.logger.debug("Failed to create subscription" + result)
                    flash("Failed to create subscription: " + result, 'error')
                    return redirect(url_for('subscription.form'))
            
        else:
            form_data = {
                'form_title': "New Subscription",
                'button_text': "Create Subscription"
            } 
            return render_template('create_subscription.html', tkn=token, name=current_user.name, email=current_user.email, **form_data)
    else:
        flash('You should login first!', 'error')
        return redirect("/")

def createAlert(entity_type, webhook_url, index_name):
    if not is_valid_url(webhook_url):
        current_app.logger.error('Invalid webhook URL format')
        flash('Invalid webhook URL format', 'error')
        return False

    url = f"{ELASTICSEARCH_URL.rstrip('/')}/{index_name}/_search"
    headersDict = {"Content-Type": "application/json"}
    query = {"match_all": {}}
    
    rule = {
        "entity_type": sanitize_string(entity_type),
        "es_url": url,
        "query": query,
        "endpoint": webhook_url,
        "headers": headersDict
    }

    config_file_path = './ES_alert_system/config.json'

    try:
        with open(config_file_path, 'r') as file:
            config_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        config_data
