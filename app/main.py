import requests
from requests.exceptions import ConnectionError, Timeout
import logging
import json
import time
from datetime import datetime, timedelta
from elastic_query import ElasticQuery
from ES_queries import ES_queries
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load polling interval from environment or use default
POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL', 10))  # in seconds

CONFIG_PATH = os.getenv('CONFIG_FILE', './config.json')
logging.info(f"Using configuration file: {CONFIG_PATH}")
logging.info(f"Polling interval set to: {POLLING_INTERVAL} seconds")
logging.info(f"Live data mode: {os.getenv('LIVE_DATA', 'true')}")
logging.info(f"Transformation type: {os.getenv('TRANSFORMATION_TYPE', 'DEME')}")
logging.info(f"========================================================")
  
def main():
    try:       
        # Initialize the queries from config
        queries = ES_queries(CONFIG_PATH)
        logging.info("Configuration file read successfully.")
        
    except Exception as e:
        logging.error(f"Failed to read configuration file: {e}", exc_info=True)
        return
        
    # Main loop - poll at regular intervals
    logging.info(f"Starting main loop with polling interval of {POLLING_INTERVAL} seconds")
    
    #Read environment variable for live data
    live_data = os.getenv('LIVE_DATA', 'true').lower() == 'true'
    
    #transformation type
    transformation_type = os.getenv('TRANSFORMATION_TYPE', 'DEME').upper()
    if transformation_type not in ['DEME', 'HOLO']:
        logging.warning(f"Invalid TRANSFORMATION_TYPE '{transformation_type}' specified. Defaulting to 'DEME'.")
        transformation_type = 'DEME'
    
    if live_data:
        logging.info("Running in live data mode.")
    else:
        logging.info("Running in n-live data mode. Static values will be used.")
        # Set the static values for testing
    static_counter = 0
    
    while True:
        loop_start = time.time()
        logging.info("Polling for new data...")
        
        for query in queries.ES_queries:
            if query.active:
                try:
                    logging.info(f"Running query for subscription: {query.subscription_id}")
                    results = query.run_query()
                    
                    #if results is None then put an empty dict
                    if results is None:
                        results = {}
                    
                    status_code = query.post_results(results, live_data = live_data, row = static_counter, transformation_type=transformation_type)  
                    
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
        
        static_counter += 1
        static_counter %= 14 # Len of the static snapshots
        # Sleep until next polling interval
        elapsed = time.time() - loop_start
        sleep_time = max(0, POLLING_INTERVAL - elapsed)
        #logging.info(f"Sleeping for {sleep_time:.2f} seconds before next poll")
        logging.info(f"Sleeping for before next poll")
        time.sleep(sleep_time)


if __name__ == "__main__":
    main()    