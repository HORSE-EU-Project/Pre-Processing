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

#static mode flag
STATIC_MODE = os.getenv('STATIC_MODE', 'false').lower() == 'true'

# Json config file path
CONFIG_FILE_PATH = os.getenv('CONFIG_FILE_PATH', './data_queries_config/config.json')
  
def main():
    try:       
        # Initialize the queries from config
        queries = ES_queries(CONFIG_FILE_PATH)
        logging.info("Configuration file read successfully.")
        
    except Exception as e:
        logging.error(f"Failed to read configuration file: {e}", exc_info=True)
        return
    
    # Check if we're in time-range iteration mode
    start_time_str = os.getenv('ES_DATA_START_TIME')
    end_time_str = os.getenv('ES_DATA_END_TIME')
    iteration_mode = False
    current_time = None
    end_time = None
    
    if start_time_str and end_time_str:
        try:
            # Parse start and end times
            start_time_str = start_time_str.replace('Z', '+00:00')
            end_time_str = end_time_str.replace('Z', '+00:00')
            current_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
            iteration_mode = True
            logging.info(f"Time-range iteration mode enabled: {start_time_str} to {end_time_str}")
            logging.info(f"Iteration interval: {POLLING_INTERVAL} seconds")
        except ValueError as e:
            logging.warning(f"Invalid ES_DATA_START_TIME or ES_DATA_END_TIME format: {e}. Falling back to continuous polling mode.")
            iteration_mode = False
    
    if not iteration_mode:
        logging.info(f"Continuous polling mode with interval of {POLLING_INTERVAL} seconds")
        logging.info(f"Each query will read data from 'now-{POLLING_INTERVAL}s' to 'now'")
    
    # Main loop
    while True:
        loop_start = time.time()
        
        if iteration_mode:
            # Check if we've reached the end time
            if current_time >= end_time:
                logging.info("Reached end time. Iteration complete.")
                break
            
            logging.info(f"Processing time window: {current_time.isoformat()}")
        else:
            logging.info("Polling for new data...")
        
        for query in queries.ES_queries:
            if query.active:
                try:
                    logging.info(f"Running query for subscription: {query.subscription_id}")
                    
                    # Pass current_time in iteration mode, or use_current_time=True in continuous mode
                    if iteration_mode and not STATIC_MODE:
                        results = query.run_query(current_time=current_time)
                    elif not iteration_mode and not STATIC_MODE:
                        results = query.run_query(use_current_time=True)
                    else:
                        results = query.run_query_static()
                    
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
        
        # Calculate elapsed time and sleep to maintain consistent interval
        elapsed = time.time() - loop_start
        sleep_time = max(0, POLLING_INTERVAL - elapsed)
        logging.info(f"Loop execution took {elapsed:.2f} seconds. Sleeping for {sleep_time:.2f} seconds before next poll")
        time.sleep(sleep_time)
        
        if iteration_mode:
            # Increment current_time by POLLING_INTERVAL
            current_time += timedelta(seconds=POLLING_INTERVAL)


if __name__ == "__main__":
    main()    