import requests
import logging
import json
import time
from datetime import datetime, timedelta
from elastic_query import ElasticQuery

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
    queries = ConfigReader.read_config('./ES_alert_system/config.json')


    #every 10 seconds run the queries
    while True:
        now = datetime.now()
        for query in queries:
            print("=========================++++++====================================")
            if not query.last_run or now >= query.last_run + query.interval:
                results = query.run_query()
                status_code = query.post_results(results)
                try:
                    
                    if status_code == 200:
                        logging.info("Query results successfully posted.")
                    else:
                        logging.warning(f"Failed to post results: HTTP {status_code}")
                except Exception as e:
                    logging.error(f"Error posting results: {e}", exc_info=True)
                query.last_run = now
        print("=============================================================")
        time.sleep(5)
        


if __name__ == "__main__":
    main()    