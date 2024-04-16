import json
from datetime import datetime, timedelta
import time
from elastic_query import ElasticQuery
import threading
import logging

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ConfigReader:
    @staticmethod
    def read_config(config_file):
        try:
            with open(config_file, 'r') as file:
                data = json.load(file)
            queries = []
            for item in data.get("rules", []):  # Use get to avoid KeyError if 'rules' is missing
                # Validate item fields
                if "es_url" in item and "index" in item and "query" in item and "headers" in item and "endpoint" in item and "interval" in item:
                    queries.append(ElasticQuery(**item))
                else:
                    logging.warning(f"Skipping invalid config item: {item}")
            return queries
        except FileNotFoundError:
            logging.error(f"Config file not found: {config_file}")
            return []
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from the config file: {config_file}; {e}")
            return []
        except Exception as e:
            logging.error(f"An unexpected error occurred while reading the config file: {e}")
            return []

def schedule_query(query):
    while True:
        try:
            now = datetime.now()
            if not query.last_run or now >= query.last_run + query.interval:
                results = query.run_query()
                status_code = query.post_results(results)
                if status_code == 200:
                    logging.info("Query results successfully posted.")
                else:
                    logging.warning(f"Failed to post results: HTTP {status_code}")
                query.last_run = now
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            logging.error("============================THREAD=================================")
        
        # Compute the next wake-up time considering the time taken by run_query and post_results
        next_run = datetime.now() + query.interval
        sleep_time = (next_run - datetime.now()).total_seconds()
        time.sleep(max(0, sleep_time))

def main():
    try:
        queries = ConfigReader.read_config('./ES_alert_system/config.json')
        threads = []
        for query in queries:
            t = threading.Thread(target=schedule_query, args=(query,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        logging.error(f"Failed during setup: {str(e)}")
        logging.error("=============================================================")

if __name__ == "__main__":
    main()
