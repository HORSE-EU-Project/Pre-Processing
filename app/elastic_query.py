import json
import requests
import logging
from datetime import datetime, timedelta
import time
from dotenv import dotenv_values

# Load environment variables from the .env file
env = dotenv_values(".env")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default values in case .env is missing some variables
ES_username = env.get('ES_USERNAME', 'elastic')
ES_password = env.get('ES_PASSWORD', 'default_password')
ES_url = env.get('ES_URL', 'http://localhost:9200')
ENDPOINT_url = env.get('ePEM_URL', 'http://localhost:8090')
ES_index = env.get('ES_INDEX', 'default_index')
INTERVAL = int(env.get('INTERVAL', 120))

# Class definition
class ElasticQuery:
    def __init__(self, subscription_id, user_id, subscription_type='ES', DB_url=ES_url, index=ES_index, 
                 query='', query_type='_count', headers={"Content-Type": "application/json"}, 
                 endpoint_url=ENDPOINT_url, interval=INTERVAL, active=True, 
                 username=ES_username, password=ES_password, **kwargs):
        self.subscription_id = subscription_id
        self.user_id = user_id
        self.subscription_type = subscription_type
        self.es_url = DB_url
        self.index = index
        self.query = query
        self.endpoint = endpoint_url
        self.headers = headers
        self.interval = timedelta(seconds=int(interval))
        self.active = active
        # Set the last_run datetime
        self.last_run = datetime(2025, 1, 31, 14, 3, 20, 729870)
        self.previous_last_run = self.last_run - self.interval
        self.username = username
        self.password = password
        self.query_type = query_type
        
        # Logging the initialized values
        logging.info(f"ES URL: {self.es_url}")
        logging.info(f"Index: {self.index}")
        logging.info(f"Query: {self.query}")
        logging.info(f"Headers: {self.headers}")
        logging.info(f"Endpoint: {self.endpoint}")
        logging.info(f"Interval: {self.interval}")
        logging.info(f"Last Run: {self.last_run}")

    def run_query(self):
        url = f"{self.es_url}/{self.index}/{self.query_type}"
        self.previous_last_run = self.last_run
        
        #put in the self.last_run the previous last run + interval
        self.last_run = self.previous_last_run + self.interval
        
        #Only for the demo #1
        self.query = self.set_query_time_window(self.previous_last_run, self.last_run, self.query)
        
        try:
            # Convert query string to dictionary if necessary
            if isinstance(self.query, str):
                qry = json.loads(self.query.replace("'", '"'))
            else:
                qry = self.query

            logging.info("=========================== Executing query ===========================")
            # logging.info("Query: %s", json.dumps(qry, indent=2))
            # logging.info("URL: %s", url)

            response = requests.post(url, data=json.dumps(qry), headers=self.headers, auth=(self.username, self.password))

            if response.status_code == 200:
                logging.info("=========Query executed successfully=========")
                results = response.json()
                dns_count = results['aggregations']['dns_packets']['doc_count']
                ntp_count = results['aggregations']['ntp_packets']['doc_count']
                
                print("From time: ", self.previous_last_run)
                print("To time: ", self.last_run)
                print("DNS count: ", dns_count)
                print("NTP count: ", ntp_count)
                print("=============================================================")
                
                return results
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
            
            if self.endpoint == 'http://192.168.130.110:8090/estimate':
                results = self.DEME_transformation(results)
                print(results)
            try:
                
                response = requests.post(self.endpoint, json=results, headers=self.headers)
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
    
    
    def set_query_time_window(self, previous_last_run, last_run, query):
        # Convert datetime objects to ISO format strings if they are not already
        if isinstance(previous_last_run, datetime):
            previous_last_run = previous_last_run.isoformat() + 'Z'
        if isinstance(last_run, datetime):
            last_run = last_run.isoformat() + 'Z'

        # Update the query object with the new timestamps
        for clause in query['query']['bool']['must']:
            if 'range' in clause and 'layers.frame.frame_frame_time' in clause['range']:
                clause['range']['layers.frame.frame_frame_time']['gte'] = previous_last_run
                clause['range']['layers.frame.frame_frame_time']['lt'] = last_run

        return query

    def DEME_transformation(self, results):
        # Extract counts from the results
        dns_count = results['aggregations']['dns_packets']['doc_count']
        ntp_count = results['aggregations']['ntp_packets']['doc_count']
        
        # Convert the last_run datetime to a Unix timestamp (seconds since the epoch)
        timestamp_unix = int(time.mktime(self.last_run.timetuple()))
        
        # Transform the results to the DEME API format
        transformed_results = [
            {
                "timestamp": str(timestamp_unix),
                "instances": [
                    {
                        "instance": "node1:Genoa RtA",
                        "features": [
                            {
                                "feature": "NTP",
                                "value": ntp_count
                            },
                            {
                                "feature": "DNS",
                                "value": dns_count
                            }
                        ]
                    }
                ]
            }
        ]
        

        
        return transformed_results


# Example usage
if __name__ == "__main__":
    endpoint = "http://192.168.130.110:8090/estimate"
    index = "packets-2024-07-09"
    headers = {'Content-Type': 'application/json'}
    username = "elastic"
    password = "HoR$e2024!eLk@sPh#ynX"
    results = [{'timestamp': '1720507497', 'instances': [{'instance': 'node1:Genoa RtA', 'features': [{'feature': 'NTP', 'value': 0}, {'feature': 'DNS', 'value': 698}]}]}]
    
    response = requests.post(endpoint, json=results, headers=headers)
    print(response.status_code)
    