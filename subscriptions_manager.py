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
            try:
                current_app.logger.debug("Open config file " + CONFIG_FILE_PATH + " for reading")
                queries = ConfigReader.read_config('./ES_alert_system/config.json')
                
                new_query = ElasticQuery(DB_url, ES_INDEX, query, {"Content-Type": "application/json"}, endpoint_url, str(interval))
                
                queries.append(new_query)
                
                #write the queries back to the config file
                with open(CONFIG_FILE_PATH, 'w') as file:
                    json.dump(data, file, indent=4)
                    current_app.logger.debug("Config file updated with new subscription.")
                return 'Subscription added successfully'
            
            except Exception as e:
                current_app.logger.debug("An unexpected error occurred: " + str(e))
                return str(e)
    
        
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