import requests
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#thoughts excerpt
class ElasticQuery:
    def __init__(self, subscription_id, user_id, subscription_type='ES', es_url='', index='test_index', query='', headers='', endpoint='', interval=10):
        if not all([es_url, index, query, headers, endpoint]):
            raise ValueError("All parameters must be provided and non-empty.")
        self.subscription_id = subscription_id
        self.user_id = user_id
        self.subscription_type = subscription_type
        self.es_url = es_url
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
        url = f"{self.es_url}/{self.index}/_search"
        try:
            response = requests.post(url, json=self.query, headers=self.headers)
            if response.status_code == 200:
                logging.info("=========Query executed successfully=========")
                return response.json()
            else:
                logging.error("Failed to execute query with status code %s", response.status_code)
                return None
        except Exception as e:
            logging.error("=========Failed to execute query=========")
            return None

    def post_results(self, results):
        """Posts query results to a specified endpoint."""
        if not results or 'hits' not in results or not results['hits'].get('hits', []):
            logging.warning("No results to post or empty results.")
            return None

        try:
            response = requests.post(self.endpoint, json=results, headers=self.headers, timeout=6)
            if response.status_code == 200:
                logging.info("Results successfully posted.")
            else:
                logging.warning("Failed to post results: HTTP %s", response.status_code)
            return response.status_code
        except Exception as e:
            logging.error("=========Error posting results=========")
            return None

    def print_results(self, results):
        """Prints query results if available."""
        if results:
            print(results)
        else:
            logging.info("No results available to print.")
