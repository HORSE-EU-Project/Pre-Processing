import json
import requests
import logging
from datetime import datetime, timedelta
import time
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default values in case .env is missing some variables
ES_username = os.getenv('ES_USERNAME', 'elastic')
ES_password = os.getenv('ES_PASSWORD', 'HoR$e2024!eLk@sPh#ynX')
ES_url = os.getenv('ES_URL', 'http://localhost:9200')
ENDPOINT_url = os.getenv('ePEM_URL', 'http://localhost:8090')
ES_index = os.getenv('ES_INDEX', 'pcap_data')
INTERVAL = int(os.getenv('INTERVAL', 120))

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
        self.username = username
        self.password = password
        self.query_type = query_type
        
        # We'll set these in run_query, no need to initialize here
        self.last_run = None
        self.previous_last_run = None
        
        # Logging the initialized values
        logging.info(f"ES URL: {self.es_url}")
        logging.info(f"Index: {self.index}")
        logging.info(f"Query: {self.query}")
        logging.info(f"Headers: {self.headers}")
        logging.info(f"Endpoint: {self.endpoint}")
        logging.info(f"Interval: {self.interval}")

    def run_query(self):
        url = f"{self.es_url}/{self.index}/{self.query_type}"

        last_data_time = os.getenv('ES_DATA_END_TIME')
        try:
            if last_data_time:
                # Convert 'Z' to '+00:00' for ISO compliance
                last_data_time = last_data_time.replace('Z', '+00:00')
                now = datetime.fromisoformat(last_data_time)
            else:
                now = datetime.now()
        except ValueError as e:
            logging.warning("Invalid ES_DATA_END_TIME format ('%s'): %s. Using current time.", last_data_time, str(e))
            now = datetime.now()

        self.previous_last_run = now - self.interval
        self.last_run = now

        try:
            # Convert query string to dictionary if necessary
            if isinstance(self.query, str):
                self.query = json.loads(self.query.replace("'", '"'))

            # Set the latest time window
            self.query = self.set_latest_time_window(self.query)

            logging.info("=========================== Executing query ===========================")
            logging.info("URL: %s", url)

            response = requests.post(url, data=json.dumps(self.query), headers=self.headers, auth=(self.username, self.password))

            if response.status_code == 200:
                logging.info("=========Query executed successfully=========")
                results = response.json()

                if isinstance(results, dict) and 'aggregations' in results:
                    # Get IP request counts
                    requests_per_ip = results['aggregations'].get('requests_per_ip', {}).get('buckets', [])

                    logging.info("From time: %s", self.previous_last_run)
                    logging.info("To time: %s", self.last_run)
                    logging.info("Requests per IP:")

                    for bucket in requests_per_ip:
                        ip = bucket.get('key')
                        count = bucket.get('doc_count')
                        logging.info("IP: %s - Count: %d", ip, count)

                    logging.info("=============================================================")

                    return results
                else:
                    logging.error("Unexpected response format: %s", results)
                    return None

        except json.JSONDecodeError as jde:
            logging.error("JSON decode error in query: %s", str(jde), exc_info=True)
            return None
        except Exception as e:
            logging.error(f"=========Failed to execute query========= {str(e)}", exc_info=True)
            return None


    def set_latest_time_window(self, query):
        try:
            if "query" in query:
                if "bool" in query["query"] and "must" in query["query"]["bool"]:
                    for clause in query["query"]["bool"]["must"]:
                        if "range" in clause and "@timestamp" in clause["range"]:
                            clause["range"]["@timestamp"]["gte"] = self.previous_last_run.isoformat()
                            clause["range"]["@timestamp"]["lte"] = self.last_run.isoformat()
                elif "range" in query["query"] and "@timestamp" in query["query"]["range"]:
                    # Direct range query
                    query["query"]["range"]["@timestamp"]["gte"] = self.previous_last_run.isoformat()
                    query["query"]["range"]["@timestamp"]["lte"] = self.last_run.isoformat()
                else:
                    logging.warning("No recognizable time range found in query.")
            else:
                logging.warning("Query does not contain a 'query' field.")
            return query
        except Exception as e:
            logging.error("Failed to set time window in query: %s", str(e))
            return query



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
    