from flask import current_app
import json
import os
from elastic_query import ElasticQuery

# Set important paths
ES_ALERT_SYSTEM_PATH = './ES_alert_system'
CONFIG_FILE_PATH = os.path.join(ES_ALERT_SYSTEM_PATH,'config.json')
ES_INDEX = 'test_index'


def add_subscription(subscription_id, user_id, subscription_type, endpoint_url, DB_url, 
                     query, interval, active, es_index='test_index', entity=None ):
        if subscription_type == 'ES':
            
            
            # Create the new rule as a dictionary
            new_rule = {
                "subscription_id": subscription_id,
                "user_id": user_id,
                "subscription_type": "ES",
                "es_url": str(DB_url),
                "index": es_index,  # Meaningful value based on the subscription type
                "query": {json.dumps(query)},  # Keep as dictionary, not string
                "headers": {"Content-Type": "application/json"},
                "endpoint": str(endpoint_url),
                "interval": interval,
                "active": active
            }

            # Open the config file in read mode and load existing data
            try:
                with open(CONFIG_FILE_PATH, 'r') as file:
                    data = json.load(file)
            except FileNotFoundError:
                data = {'rules': []}  # Initialize if file doesn't exist

            # Append the new rule to the list of rules
            data['rules'].append(new_rule)

            # Write the updated data back to the config file
            try:
                with open(CONFIG_FILE_PATH, 'w') as file:
                    json.dump(data, file, indent=4)
                
                current_app.logger.debug("New rule added successfully.")
            except FileNotFoundError:
                current_app.logger.debug("The configuration file was not found.")
            except json.JSONDecodeError:
                current_app.logger.debug("The configuration file contains invalid JSON.")
            except Exception as e:
                current_app.logger.debug(f"An unexpected error occurred: {str(e)}")
    
        
def update_subscription(subscription_id, user_id, subscription_type, endpoint_url, DB_url, 
                        query, interval, active, es_index='test_index', es_index=None, entity=None ):
    try:
        if subscription_type == 'ES':
            key, value = query.split(':')
            # Remove any leading/trailing whitespace
            key = key.strip()
            value = value.strip()
            value = eval(value)
            
            es_query = {"query": {key: value}}
            
            with open(CONFIG_FILE_PATH, 'r') as file:
                data = json.load(file)
                #search for the subscription_id and update the subscription
                for rule in data['rules']:
                    if rule['subscription_id'] == subscription_id:
                        rule['user_id'] = user_id
                        rule["subscription_type"] = "ES"
                        rule['es_url'] = DB_url
                        rule['index'] = es_index
                        rule['query'] = json.dumps(es_query)
                        rule['headers'] = {"Content-Type": "application/json"}
                        rule['endpoint'] = endpoint_url
                        rule['interval'] = interval
                        break
            with open(CONFIG_FILE_PATH, 'w') as file:
                json.dump(data, file, indent=4)
    except EOFError as e:
        return str(e)
    return 'Subscription updated successfully'

def delete_subscription(subscription_id, subscription_type):
    try:
        if subscription_type == 'ES':
            with open(CONFIG_FILE_PATH, 'r') as file:
                data = json.load(file)
                #search for the subscription_id and update the subscription
                for rule in data['rules']:
                    if rule['subscription_id'] == subscription_id:
                        data['rules'].remove(rule)
                        break
            with open(CONFIG_FILE_PATH, 'w') as file:
                json.dump(data, file, indent=4)
    except EOFError as e:
        return str(e)
    return 'Subscription deleted successfully'



def sync_subscriptions(subscriptions):
    try:
        if not subscriptions:
            return "No subscriptions found for the user."

        # Convert Row objects to dictionaries if necessary
        dict_subscriptions = [dict(sub) for sub in subscriptions] if subscriptions else []

        #convert the values of the keys "updated_at" and "created_at" to string
        for sub in dict_subscriptions:
            sub['updated_at'] = str(sub['updated_at'])
            sub['created_at'] = str(sub['created_at'])
        
        # Only for ES subscriptions for now
        data = {'rules': dict_subscriptions}
        with open(CONFIG_FILE_PATH, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        
        return "Subscriptions successfully synced to the YAML file."
    except Exception as e:
        return f"An error occurred while syncing subscriptions: {str(e)}"