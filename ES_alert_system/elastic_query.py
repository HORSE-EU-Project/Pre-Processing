import json
import requests
import logging
from datetime import datetime, timedelta
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ES_username = 'elastic'
ES_password = 'HoR$e2024!eLk@sPh#ynX'

# Predefined snapshots of NTP and DNS counts
SNAPSHOTS = [
    (34, 3060),
    (34, 2970),
    (33, 2970),
    (35, 2970),
    (38, 3150),
    (47, 2970),
    (62, 2970),
    (75, 3150),
    (80, 3060),
    (77, 2970),
    (61, 3150),
    (49, 3060),
    (39, 2970),
    (35, 3060)
]



class ElasticQuery:
    def __init__(self, subscription_id, user_id, subscription_type='ES', DB_url='', index='packets-2024-07-09', 
                 query='', query_type = '_count', headers = {"Content-Type": "application/json"}, endpoint_url='', interval=120, active=True, 
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
        # Initialize last_run to start time
        self.last_run = datetime(2024, 7, 9, 9, 9, 33, 540984)
        self.previous_last_run = self.last_run - self.interval
        
        self.username = username
        self.password = password
        self.query_type = query_type
        self.snapshot_index = 0  # To keep track of which snapshot to use
        
        print("ES URL: ", self.es_url)
        print("Index: ", self.index)
        print("Query: ", self.query)
        print("Headers: ", self.headers)
        print("Endpoint: ", self.endpoint)
        print("Interval: ", self.interval)
        print("Last Run: ", self.last_run)

    def run_query(self):
        if self.snapshot_index < len(SNAPSHOTS):
            # Use predefined snapshot values instead of querying the database
            ntp_count, dns_count = SNAPSHOTS[self.snapshot_index]
            
            # Move to the next snapshot index
            self.snapshot_index += 1
            
            # Create mock results
            results = {
                'aggregations': {
                    'dns_packets': {'doc_count': dns_count},
                    'ntp_packets': {'doc_count': ntp_count}
                }
            }
            
            logging.info("=========Query executed successfully=========")
            return results
        else:
            logging.info("=========Results to process=========")
            return None

    def post_results(self, results):
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
            self.active = False
    
    def set_query_time_window(self, previous_last_run, last_run, query):
        # This method remains unchanged as it's not needed for the demo
        pass

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
    