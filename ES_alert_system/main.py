import requests
from requests.exceptions import ConnectionError, Timeout
import logging
import json
import time
from datetime import datetime, timedelta
from elastic_query import ElasticQuery
import ES_queries

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ConfigReader:
    @staticmethod
    def read_config(config_file):
        with open(config_file, 'r') as file:
            data = json.load(file)
            return [ElasticQuery(**item) for item in data["rules"]]

  
def main():
    #Read the configuration file
    try:
        
        # queries = ConfigReader.read_config('./ES_alert_system/config.json')
        queries = ES_queries('./ES_alert_system/config.json')
        
        logging.info("Configuration file read successfully.")
    except Exception as e:
        logging.error(f"Failed to read configuration file: {e}", exc_info=True)
        return

    #every 10 seconds run the queries
    while True:
        now = datetime.now()
        for query in queries:
            print("=========================++++++====================================")
            if not query.last_run or now >= query.last_run + query.interval:
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
                    
                query.last_run = now
        print("=============================================================")
        time.sleep(10)
        


if __name__ == "__main__":
    main()    