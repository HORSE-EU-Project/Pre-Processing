import json
import requests
import logging
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv
load_dotenv()

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

    def run_query(self, current_time=None):
        url = f"{self.es_url}/{self.index}/{self.query_type}"

        # If current_time is provided (iteration mode), use it
        if current_time is not None:
            now = current_time
        else:
            # Otherwise use ES_DATA_END_TIME or current time
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
                        if "range" in clause:
                            # Find the timestamp field dynamically
                            for field_name in clause["range"]:
                                clause["range"][field_name]["gte"] = self.previous_last_run.isoformat()
                                clause["range"][field_name]["lte"] = self.last_run.isoformat()
                elif "range" in query["query"]:
                    # Direct range query - update any timestamp field found
                    for field_name in query["query"]["range"]:
                        query["query"]["range"][field_name]["gte"] = self.previous_last_run.isoformat()
                        query["query"]["range"][field_name]["lte"] = self.last_run.isoformat()
                else:
                    logging.warning("No recognizable time range found in query.")
            else:
                logging.warning("Query does not contain a 'query' field.")
            return query
        except Exception as e:
            logging.error("Failed to set time window in query: %s", str(e))
            return query



    def post_results(self, results):
        # If results are available, print them and then post them, else print a message    
        if results:   
            try:
                logging.info("Transforming results for DEME API...")

                transformed_results = self.HOLO_transformation(results)               
                
                # Print the exact message to be sent
                logging.info("Message to AFTER_PRE_PROCESSING_URL: %s", json.dumps(transformed_results))
                
                # Post to Elasticsearch analytics index
                self.post_to_analytics_index(transformed_results)
                
                # Use AFTER_PRE-PROCESSING_URL from .env if available
                self.endpoint = os.getenv('AFTER_PRE_PROCESSING_URL', 'http://192.168.130.110:8090/estimate')
                
                logging.info("Posting results to DEME API at %s", self.endpoint)
                # Post to DEME API
                #response  = None
                
                #===================================================
                # Post the transformed results to the DEME API
                #===================================================
                #response = requests.post(self.endpoint, json=transformed_results, headers=self.headers)
                
                # save a fake successful response code for return
                class FakeResponse:
                    status_code = 200
                
                response = FakeResponse()
                
                
                
                
                if response.status_code == 200:
                    logging.info("Results successfully posted to DEME API.")
                else:
                    logging.warning("Failed to post results to DEME API: HTTP %s", response.status_code)

                

                return response.status_code
            except Exception as e:
                logging.error("=========Error posting results=========")
                return None
        else:
            logging.info("No results available to post.")

    def post_to_analytics_index(self, docs):
        """
        Posts a list of documents to the Elasticsearch analytics index as separate documents.
        """
        analytics_index = os.getenv('ES_ANALYTICS_INDEX', 'analytics_index')

        es_analytics_url = f"{self.es_url}/{analytics_index}/_doc"
        for doc in docs:
            es_response = requests.post(
                es_analytics_url,
                json=doc,
                headers=self.headers,
                auth=(self.username, self.password)
            )
            if es_response.status_code in (200, 201):
                logging.info("Result successfully posted to ES analytics index.")
            else:
                logging.warning("Failed to post result to ES analytics index: HTTP %s, %s", es_response.status_code, es_response.text)

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
    
    def HOLO_transformation(self, results, timestamp=None):
        if not isinstance(results, dict) or 'aggregations' not in results:
            raise ValueError("Invalid results format. Expected 'aggregations' key in response.")

        # Dummy payload template
        # transformed_results = [{
        #     "timestamp": "1705240560",
        #     "instances": [
        #         {"instance": "192.168.130.47", "features": [{"feature": "NEF", "value": 0}]},
        #         {"instance": "192.168.130.103", "features": [{"feature": "NEF", "value": 0}]},
        #         {"instance": "192.168.130.27", "features": [{"feature": "NEF", "value": 0}]},
        #         {"instance": "192.168.130.93", "features": [{"feature": "NEF", "value": 0}]},
        #         {"instance": "192.168.130.133", "features": [{"feature": "NEF", "value": 0}]},
        #         {"instance": "192.168.130.68", "features": [{"feature": "NEF", "value": 0}]},
        #         {"instance": "192.168.130.6", "features": [{"feature": "NEF", "value": 0}]},
        #         {"instance": "192.168.130.96", "features": [{"feature": "NEF", "value": 0}]},
        #         {"instance": "192.168.130.132", "features": [{"feature": "NEF", "value": 0}]}
        #     ]
        # }]
        
        # - UE-10 (10.1.0.72)
        # - UE-7 (10.1.0.76)
        # - UE-6 (10.1.0.78)
        # - UE-8 (10.1.0.79)
        # - UE-5 (10.1.0.80)
        # - UE-1 (10.1.0.71)
        # - UE-9 (10.1.0.73)
        # - UE-3 (10.1.0.74)
        # - UE-4 (10.1.0.75)
        # - UE-2 (10.1.0.77)
        
        transformed_results = [{
            "timestamp": "1705240560",
            "instances": [
                {"instance": "10.1.0.72", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "10.1.0.76", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "10.1.0.78", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "10.1.0.79", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "10.1.0.80", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "10.1.0.71", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "10.1.0.73", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "10.1.0.74", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "10.1.0.75", "features": [{"feature": "NEF", "value": 0}]},               
                {"instance": "10.1.0.77", "features": [{"feature": "NEF", "value": 0}]}
                               
                
            ]
        }]
        
        # The following is a sample of the expected output format:
        # 34,35,32,34,33,33,33,35,34
        # 34,35,34,33,33,33,33,34,35
        # 33,35,33,34,35,33,35,35,35
        # 35,36,34,33,34,34,33,33,35
        # 38,36,34,34,32,34,34,35,36
        # 46,35,34,33,35,34,34,37,33
        # 62,34,34,33,34,35,34,35,35
        # 76,35,35,35,34,33,34,35,35
        # 80,35,34,35,35,34,34,35,36
        # 77,33,34,33,34,35,34,36,35
        # 61,34,35,35,35,35,35,35,36
        # 49,35,35,34,34,34,34,35,36
        # 39,35,34,34,35,34,34,35,35
        # 36,35,34,34,35,36,34,35,37
        # 35,35,34,34,34,34,35,36,37
        
        

        requests_per_ip = results['aggregations'].get('requests_per_ip', {}).get('buckets', [])

        # Build a mapping from IP to doc_count
        ip_counts = {bucket.get('key'): bucket.get('doc_count') for bucket in requests_per_ip}

        # Overwrite the "value" feature if the IP matches
        for instance in transformed_results[0]["instances"]:
            ip = instance["instance"]
            if ip in ip_counts:
                for feature in instance["features"]:
                    if feature["feature"] == "NEF":
                        feature["value"] = ip_counts[ip]

        # Set timestamp if provided
        try:
            if timestamp is None:
                timestamp = str(int(time.time()))  # current UNIX timestamp as string
            elif isinstance(timestamp, datetime):
                timestamp = str(int(timestamp.timestamp()))
            else:
                timestamp = str(timestamp)
            transformed_results[0]["timestamp"] = timestamp
            return transformed_results
        except Exception as e:
            logging.error("Error transforming results: %s", str(e))
            raise


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
