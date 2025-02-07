import requests
from requests.exceptions import ConnectionError, Timeout
import logging
import json
import time
from datetime import datetime, timedelta
from elastic_query import ElasticQuery
from ES_queries import ES_queries
from dotenv import dotenv_values
from datetime import datetime

# Load environment variables from the .env file
env = dotenv_values(".env")

# Load ES_DATA_END_TIME from .env and parse it
ES_DATA_END_TIME = env.get('ES_DATA_END_TIME')

if ES_DATA_END_TIME:
    try:
        # Convert ES_DATA_END_TIME to a datetime object
        ES_DATA_END_TIME = datetime.fromisoformat(ES_DATA_END_TIME.rstrip('Z'))
    except ValueError:
        raise ValueError("Invalid datetime format for ES_DATA_END_TIME in .env file.")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ConfigReader:
    @staticmethod
    def read_config(config_file):
        with open(config_file, 'r') as file:
            data = json.load(file)
            return [ElasticQuery(**item) for item in data["rules"]]

  
def main():
    
    try:
                
        # queries = ConfigReader.read_config('./ES_alert_system/config.json')
        queries = ES_queries('./config.json')
        
        logging.info("Configuration file read successfully.")
    except Exception as e:
        logging.error(f"Failed to read configuration file: {e}", exc_info=True)
        
    #every 10 seconds run the queries
    flag = True
    while flag:
            #Read the configuration file
        
        
        now = datetime.now()
        for query in queries.ES_queries:
            print("=========================++++++====================================")
            if (not query.last_run or now >= query.last_run + query.interval) and query.active:
                try:
                    results = query.run_query()
                    status_code = query.post_results(results)  
                    if status_code == 200:
                        logging.info("Query results successfully posted.")
                    else:
                        logging.warning(f"Failed to post results: HTTP {status_code}")
                except Timeout:
                    logging.error("The request timed out")
                except ConnectionError:
                    logging.error("The request failed to connect")
                except requests.HTTPError as e:
                    logging.error(f"HTTP error occurred: {e}")
                except Exception as e:
                    logging.error(f"An unexpected error occurred: {e}")
            #if query.last_run is larger that ES_DATA_END_TIME print the message
            if query.last_run > ES_DATA_END_TIME:
                print("==========================Query reached the end of the data============================")
                query.active = False
                flag = False        
                #query.last_run = now
        print("=============================================================")
        # time.sleep(3)

        


if __name__ == "__main__":
    main()    