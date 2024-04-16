import requests
import logging
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ElasticQuery:
    def __init__(self, es_url, index, query, headers, endpoint, interval=10):
        if not all([es_url, index, query, headers, endpoint]):
            raise ValueError("All parameters must be provided and non-empty.")
        
        self.es = Elasticsearch([es_url])
        self.index = index  # Dynamic index name
        self.query = query
        self.endpoint = endpoint
        self.headers = headers
        self.interval = timedelta(seconds=interval)
        self.last_run = None

    def run_query(self):
        try:
            response = self.es.search(index=self.index, body=self.query)
            logging.info("Query executed successfully.")
            return response
        except Exception as e:
            logging.error(f"Failed to execute query: {e}")
            return None

    def post_results(self, results):
        if results is None:
            logging.warning("No results to post.")
            return None

        try:
            response = requests.post(self.endpoint, json=results, headers=self.headers)
            if response.status_code == 200:
                logging.info("Results successfully posted.")
            else:
                logging.warning(f"Failed to post results: HTTP {response.status_code}")
            return response.status_code
        except Exception as e:
            logging.error(f"Error posting results: {e}")
            return None

    def print_results(self, results):
        if results:
            print(results)
        else:
            logging.info("No results available to print.")
