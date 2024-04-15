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
        with open(config_file, 'r') as file:
            data = json.load(file)
            return [ElasticQuery(**item) for item in data["queries"]]

def schedule_query(query):
    while True:
        try:
            if not query.last_run or datetime.now() >= query.last_run + query.interval:
                results = query.run_query()
                status_code = query.post_results(results)
                if status_code == 200:
                    logging.info("Query results successfully posted.")
                else:
                    logging.warning(f"Failed to post results: HTTP {status_code}")
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
        
        # Compute the next wake-up time considering the time taken by run_query and post_results
        next_run = datetime.now() + query.interval
        sleep_time = (next_run - datetime.now()).total_seconds()
        time.sleep(max(0, sleep_time))

def main():
    try:
        queries = ConfigReader.read_config('config.json')
        threads = []
        for query in queries:
            t = threading.Thread(target=schedule_query, args=(query,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        logging.error(f"Failed during setup: {str(e)}")

if __name__ == "__main__":
    main()
