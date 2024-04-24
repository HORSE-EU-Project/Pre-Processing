#Functions for updating  the subscriptions for various endpoints and sources

# Set important paths
ES_ALERT_SYSTEM_PATH = './ES_alert_system'
CONFIG_FILE_PATH = f'{ES_ALERT_SYSTEM_PATH}/config.json'

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def update_subscriptions(user_id, subscription_type, endpoint_url, DB_url, query, interval, active):
    try:
        # Update the ./ES_alert_system/config.json file with the new subscription if subscription type is 'ES'
        if subscription_type == 'ES':
            with open(CONFIG_FILE_PATH, 'r') as file:
                data = json.load(file)
                data['rules'].append({
                    "es_url": DB_url,
                    "index": "logs",
                    "query": query,
                    "headers": {"Content-Type": "application/json"},
                    "endpoint": endpoint_url,
                    "interval": interval
                })
            with open(CONFIG_FILE_PATH, 'w') as file:
                json.dump(data, file, indent=4)
                
    except sqlite3.IntegrityError as e:
        return str(e)
    return 'Subscription stored successfully'
