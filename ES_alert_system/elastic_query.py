import json
import requests
import logging
from datetime import datetime, timedelta
import DEMO_functions as fun

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ES_username = 'elastic'
ES_password = 'HoR$e2024!eLk@sPh#ynX'

#thoughts excerpt
class ElasticQuery:
    def __init__(self, subscription_id, user_id, subscription_type='ES', DB_url='', index='packets-2024-07-09', 
                 query='', headers = {"Content-Type": "application/json"}, endpoint_url='', interval=10, active=True, 
                 username=ES_username, password=ES_password, **kwargs):
        self.subscription_id = subscription_id
        self.user_id = user_id
        self.subscription_type = subscription_type
        self.es_url = DB_url
        self.index = index
        self.query = query
        self.endpoint = endpoint_url
        self.headers = headers
        self.interval = timedelta(seconds= int(interval))
        self.active = active
        self.last_run = None
        self.username = username
        self.password = password
        
        print("ES URL: ", self.es_url)
        print("Index: ", self.index)
        print("Query: ", self.query)
        print("Headers: ", self.headers)
        print("Endpoint: ", self.endpoint)
        print("Interval: ", self.interval)
        print("Last Run: ", self.last_run)

    def run_query(self):
        url = f"{self.es_url}/{self.index}/_count"
        try:
            # Convert query string to dictionary if necessary
            if isinstance(self.query, str):
                qry = json.loads(self.query.replace("'", '"'))
            else:
                qry = self.query

            logging.info("=========================== Executing query ===========================")
            logging.info("Query: %s", json.dumps(qry, indent=2))
            logging.info("URL: %s", url)

            response = requests.post(url, data=json.dumps(qry), headers=self.headers, auth=(self.username, self.password))

            if response.status_code == 200:
                logging.info("=========Query executed successfully=========")
                return response.json()
            else:
                logging.error("Failed to execute query with status code %s", response.status_code)
                logging.error("Response: %s", response.text)
                return None
        except Exception as e:
            logging.error("=========Failed to execute query=========", str(e))
            return None



    def post_results(self, results):
        #if results are available print them and then post them, else print a message    
        if results:
            print(results)
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
        else:
            logging.info("No results available to post.")
    

# Example usage
if __name__ == "__main__":
    es_url = "http://192.168.130.48:9200"
    index = "packets-2024-07-09"
    headers = {'Content-Type': 'application/json'}
    username = "elastic"
    password = "HoR$e2024!eLk@sPh#ynX"
    
    query = '''
    {
      "query": {
        "bool": {
          "must": [
            {
              "exists": {
                "field": "layers.ip"
              }
            },
            {
              "exists": {
                "field": "layers.udp"
              }
            },
            {
              "exists": {
                "field": "layers.ntp"
              }
            },
            {
              "term": {
                "layers.udp.udp_udp_dstport": 123
              }
            }
          ]
        }
      }
    }
    '''
    
    executor = ElasticQuery(es_url, index, headers, username, password, query)
    result = executor.run_query()

    if result:
        print("Query Result:", json.dumps(result, indent=2))
    else:
        print("Query failed.")
    