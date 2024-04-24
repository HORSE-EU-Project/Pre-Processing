from flask import current_app
import json
import os
from elastic_query import ElasticQuery

# Set important paths
ES_ALERT_SYSTEM_PATH = './ES_alert_system'
CONFIG_FILE_PATH = os.path.join(ES_ALERT_SYSTEM_PATH,'config.json')
ES_INDEX = 'test_index'

class ConfigReader:
    @staticmethod
    def read_config(config_file):
        with open(config_file, 'r') as file:
            data = json.load(file)
            return [ElasticQuery(**item) for item in data["rules"]]




def add_subscription(subscription_id, user_id, subscription_type, endpoint_url, DB_url, query, interval, active):
        if subscription_type == 'ES':
            # Create the new rule as a dictionary
            new_rule = {
                "subscription_id": subscription_id,
                "user_id": user_id,
                "es_url": DB_url,
                "index": "your_index_based_on_subscription_type",  # Set this to a meaningful value based on the subscription type
                "query": query,
                "headers": {"Content-Type": "application/json"},
                "endpoint": endpoint_url,
                "interval": interval,
                "active": active
            }
            
            try:
        # Open the config file in read mode and load existing data
                with open(config_file_path, 'r') as file:
                    data = json.load(file)
                
                # Append the new rule to the list of rules
                data['rules'].append(new_rule)

                # Write the updated data back to the config file
                with open(config_file_path, 'w') as file:
                    json.dump(data, file, indent=4)
                
                current_app.logger.debug("New rule added successfully.")
            except FileNotFoundError:
                current_app.logger.debug("The configuration file was not found.")
            except json.JSONDecodeError:
                current_app.logger.debug("The configuration file contains invalid JSON.")
            except Exception as e:
                current_app.logger.debug(f"An unexpected error occurred: {str(e)}")
    
        
def update_subscription(subscription_id, user_id, subscription_type, endpoint_url, DB_url, query, interval, active):
    try:
        # Update the ./ES_alert_system/config.json file with the new subscription if subscription type is 'ES'
        if subscription_type == 'ES':
            with open(CONFIG_FILE_PATH, 'r') as file:
                data = json.load(file)
                #search for the subscription_id and update the subscription
                for rule in data['rules']:
                    if rule['subscription_id'] == subscription_id:
                        rule['user_id'] = user_id
                        rule['es_url'] = DB_url
                        rule['index'] = ES_INDEX
                        rule['query'] = query
                        rule['headers'] = {"Content-Type": "application/json"}
                        rule['endpoint'] = endpoint_url
                        rule['interval'] = interval
                        break
            with open(CONFIG_FILE_PATH, 'w') as file:
                json.dump(data, file, indent=4)
    except EOFError as e:
        return str(e)
    return 'Subscription updated successfully'

def delete_subscription(subscription_id):
    try:
        # Update the ./ES_alert_system/config.json file with the new subscription if subscription type is 'ES'
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