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

        # Initialize Elasticsearch client with headers specific for Elasticsearch if needed
        self.es = Elasticsearch([es_url], headers={'Content-Type': 'application/json'})
        self.index = index
        self.query = query
        self.endpoint = endpoint
        self.headers = headers
        self.interval = timedelta(seconds=interval)
        self.last_run = None
        
        print("ES URL: ", es_url)
        print("Index: ", index)
        print("Query: ", query)
        print("Headers: ", headers)
        print("Endpoint: ", endpoint)
        print("Interval: ", interval)
        print("Last Run: ", self.last_run)
        

    def run_query(self):
        """Executes a query on Elasticsearch and returns the results."""
        try:
            response = self.es.search(index=self.index, body=self.query)
            logging.info("Query executed successfully: %s", response)
            return response
        except Exception as e:
            logging.error("Failed to execute query: %s", e, exc_info=True)
            return None

    def post_results(self, results):
        """Posts query results to a specified endpoint."""
        if not results or 'hits' not in results or not results['hits'].get('hits', []):
            logging.warning("No results to post or empty results.")
            return None

        try:
            response = requests.post(self.endpoint, json=results, headers=self.headers)
            if response.status_code == 200:
                logging.info("Results successfully posted.")
            else:
                logging.warning("Failed to post results: HTTP %s", response.status_code)
            return response.status_code
        except Exception as e:
            logging.error("Error posting results: %s", e, exc_info=True)
            return None

    def print_results(self, results):
        """Prints query results if available."""
        if results:
            print(results)
        else:
            logging.info("No results available to print.")
