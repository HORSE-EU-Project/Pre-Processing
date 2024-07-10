from flask import current_app
import json
import os
from elastic_query import ElasticQuery
import traceback
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set important paths
ES_ALERT_SYSTEM_PATH = os.getenv('ES_ALERT_SYSTEM_PATH', './ES_alert_system')
CONFIG_FILE_PATH = os.path.join(ES_ALERT_SYSTEM_PATH, 'config.json')
ES_INDEX = os.getenv('ES_INDEX', 'test_index')
ORION_URL = os.getenv('ORION_URL', 'http://orion:1026')


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
                return 'Subscription added successfully'
            except Exception as e:
                current_app.logger.debug(f"An unexpected error occurred: {str(e)}")
                traceback_str = traceback.format_exc()
                return traceback_str

        #else if subscription_type is 'ORION', add the subscription to the Orion Context Broker
        elif subscription_type == 'ORION':
            try:
                result = createOrionRequest(str(entity), str(endpoint_url))
                return result           

            
            except Exception as e:
                traceback_str = traceback.format_exc()
                return traceback_str
        
        
def update_subscription(subscription_id, user_id, subscription_type, endpoint_url, DB_url, 
                        query, interval, active, es_index='test_index', entity=None ):
    try:
        if subscription_type == 'ES':
            
            with open(CONFIG_FILE_PATH, 'r') as file:
                data = json.load(file)
                #search for the subscription_id and update the subscription
                for rule in data['rules']:
                    if rule['subscription_id'] == subscription_id:
                        rule['user_id'] = user_id
                        rule["subscription_type"] = "ES"
                        rule['es_url'] = DB_url
                        rule['index'] = es_index
                        rule['query'] = json.dumps(query)
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
        elif subscription_type == 'ORION':
            result = deleteOrionSubscription(subscription_id)
            return result
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
        
        #only keep the subscriptions that have subscription_type as 'ES'
        dict_subscriptions = [sub for sub in dict_subscriptions if sub['subscription_type'] == 'ES']
        
        # Only for ES subscriptions for now
        data = {'rules': dict_subscriptions}
        with open(CONFIG_FILE_PATH, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        
        return "Subscriptions successfully synced to the YAML file."
    except Exception as e:
        return f"An error occurred while syncing subscriptions: {str(e)}"
    
    
def createOrionRequest(dbName, endpoint):
    url = ORION_URL+"/v2/subscriptions/"
    headersDict = {"Content-Type" : "application/json"}
    payload = dict( description = dbName,
                    subject = {"entities" : [], "condition" : {"attrs" : []}},
                    notification = {"http" : {"url": ""}, "attrs" : [], "metadata" : ["dateCreated", "dateModified"]}                
                    )
    payload["subject"]["entities"] = [{"idPattern": ".*","type":dbName}]
    payload["notification"]["http"]["url"] = endpoint
    return sendRequestToFiware(url, headersDict, payload)

def deleteOrionSubscription(subscription_id):
    url = ORION_URL + "/v2/subscriptions/" + subscription_id
    headers = {"Content-Type": "application/json"}
    
    try:
        r = requests.delete(url, headers=headers)
        if r.status_code == 204:
            return 'Subscription deleted successfully'
        else:
            return 'Failed to delete subscription'
    except requests.exceptions.RequestException as e:
        return str(e)

#Sending a request to fiware       
def sendRequestToFiware(matchPostURL,headersDict,matchPayload):
    try:
        current_app.logger.debug(f"Sending request to Fiware: {matchPostURL}")
        r = requests.post(matchPostURL, headers = headersDict, data= json.dumps(matchPayload))
        # if r.status_code == 201:
        if r.status_code == 201:
            subscription_id = r.headers.get("Location").split("/")[-1]
            return subscription_id
        else:
            current_app.logger.debug(f"Failed to create subscription. Status code: {r.status_code}, Response: {r.text}")
            return None
    except requests.exceptions.RequestException as e:
        current_app.logger.debug(f"Error sending request to Fiware: {str(e)}")
        return None
    except json.decoder.JSONDecodeError as je:
        current_app.logger.debug(f"Error decoding response JSON: {str(je)}, Response text: {r.text}")
        return None
    except requests.exceptions.RequestException as e:
        traceback_str = traceback.format_exc()
        current_app.logger.debug(str(traceback_str))
        return traceback_str