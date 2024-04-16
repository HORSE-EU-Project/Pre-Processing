import requests
import logging
import json
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ElasticQuery:
    def __init__(self, es_url, index, query, headers, endpoint, interval=10):
        if not all([es_url, index, query, headers, endpoint]):
            raise ValueError("All parameters must be provided and non-empty.")

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
                logging.info("Query executed successfully: %s", response.json())
                return response.json()
            else:
                logging.error("Failed to execute query with status code %s: %s", response.status_code, response.text)
                return None
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

class ConfigReader:
    @staticmethod
    def read_config(config_file):
        with open(config_file, 'r') as file:
            data = json.load(file)
            return [ElasticQuery(**item) for item in data["rules"]]

  
def main():
    #Read the configuration file
    queries = ConfigReader.read_config('./ES_alert_system/config.json')
    
    #Loop through the queries and run them
    # for query in queries:
    #     print("Query ES URL: ", query.es_url)
    #     print("Query Index: ", query.index)
    #     print("Query Query: ", query.query)
    #     print("Query Headers: ", query.headers)
    #     print("Query Endpoint: ", query.endpoint)
    #     print("Query Interval: ", query.interval)
    #     print("Query Last Run: ", query.last_run)
    #     print("====================================================")
        
    #     results = query.run_query()
    #     status_code = query.post_results(results)
    #     query.print_results(results)
    
    
    
    
    
    #every 10 seconds run the queries
    while True:
        now = datetime.now()
        for query in queries:
            print("=========================++++++====================================")
            if not query.last_run or now >= query.last_run + query.interval:
                results = query.run_query()
                status_code = query.post_results(results)
                if status_code == 200:
                    logging.info("Query results successfully posted.")
                else:
                    logging.warning(f"Failed to post results: HTTP {status_code}")
                #query.last_run = now
        print("=============================================================")
        time.sleep(5)
        
    
    # # Define the Elasticsearch URL
    # es_url = "http://localhost:9200"
    
    # # Define the index to query
    # index = "test_index"
    
    # # Define the query to execute
    # query = {
    #     "query": {
    #         "match_all": {}
    #     }
    # }
    
    # # Define the headers for the HTTP requests
    # headers = {"Content-Type": "application/json"}
    
    # # Define the endpoint to post the results
    # endpoint = "http://localhost:5000/dff-data"
    
    # # Create an instance of the ElasticQuery class
    # query_instance = ElasticQuery(es_url, index, query, headers, endpoint)
    
    # print("Query 2 ES URL: ", query_instance.es_url)
    # print("Query 2 Index: ", query_instance.index)
    # print("Query 2 Query: ", query_instance.query)
    # print("Query 2 Headers: ", query_instance.headers)
    # print("Query 2 Endpoint: ", query_instance.endpoint)
    # print("Query 2 Interval: ", query_instance.interval)
    # print("Query 2 Last Run: ", query_instance.last_run)
    # print("====================================================")
    
    # # Run the query
    # results = query_instance.run_query()
    
    # # Post the results
    # status_code = query_instance.post_results(results)
    
    # # Print the results
    # #query_instance.print_results(results)

if __name__ == "__main__":
    main()    