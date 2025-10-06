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

UPC_node_ip="192.168.130.103"
CNIT_node_ip="192.168.130.47"



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
                logging.info("=========Query executed=========")
                results = response.json()

                if isinstance(results, dict) and 'aggregations' in results:
                    # Get IP request counts
                    logging.info("=========Results are the following=========")
                    #results = response.json()
                    #dns_count = results['aggregations']['dns_packets']['doc_count']
                    #ntp_count = results['aggregations']['ntp_packets']['doc_count']
                    
                    logging.info("Query results: %s", json.dumps(results, indent=2))
                    
                    
                    logging.info("From time: %s", self.previous_last_run)
                    logging.info("To time: %s", self.last_run)
                    #logging.info("DNS count: %s", dns_count)
                    #logging.info("NTP count: %s", ntp_count)
                    logging.info("=============================================================")

                    return results
                else:
                    logging.error("Unexpected response format: %s", results)
                    return None
            else:
                logging.error("Failed to execute query: HTTP %s, %s", response.status_code, response.text)
                return None
        except json.JSONDecodeError as jde:
            logging.error("JSON decode error in query: %s", str(jde), exc_info=True)
            return None
        except Exception as e:
            logging.error(f"=========Failed to execute query========= {str(e)}")
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



    def post_results(self, results, live_data=False, row=-1, transformation_type='DEME'):
        # If results are available, print them and then post them, else print a message    
        if results and live_data:
            logging.info("Transforming results for DEME API...")
            if transformation_type == 'HOLO':
                transformed_results = self.HOLO_transformation(results)
            elif transformation_type == 'DEME_MULTIDOMAIN':
                logging.info("Transforming results for DEME_MULTIDOMAIN API...")
                transformed_results = self.DEME_transformation_multidomain(results)
            else:
                transformed_results = self.DEME_transformation(results)
        elif not live_data and row >= 0 and row < len(SNAPSHOTS):
            logging.info("Posting results for instance: %d", row)
            ntp_count, dns_count = SNAPSHOTS[row]
            
            # Create mock results
            results = {
                'aggregations': {
                    'dns_packets': {'doc_count': dns_count},
                    'ntp_packets': {'doc_count': ntp_count}
                }
            }
            if transformation_type == 'DEME_MULTIDOMAIN':
                transformed_results = self.DEME_transformation_multidomain(results, row=row)
            else:
                transformed_results = self.DEME_transformation(results)
        else:
            logging.info("No results available to post.")
                
        try:    
            
            
            
            # Post to Elasticsearch analytics index
            self.post_to_analytics_index(transformed_results)
            
            # Use AFTER_PRE_PROCESSING_URL from .env if available
            self.endpoint = os.getenv('AFTER_PRE_PROCESSING_URL', 'http://192.168.130.110:8090/estimate')

            logging.info("Posting results to DEME API at %s", self.endpoint)
            # Print the exact JSON message to be sent
            logging.info("JSON message to AFTER_PRE_PROCESSING_URL: %s", json.dumps(transformed_results, indent=2))
            #Print the endpoint URL
            logging.info("Endpoint URL: %s", self.endpoint)
            
            # Post the transformed results to the DEME API
            response = requests.post(self.endpoint, json=transformed_results, headers=self.headers)
            
            if response.status_code == 200:
                logging.info("Results successfully posted to DEME API.")
            else:
                logging.warning("Failed to post results to DEME API: HTTP %s", response.status_code)

            return response.status_code
        except Exception as e:
            logging.error("=========Error posting results=========")
            return None
        

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
        #dns_count = results['aggregations']['dns_packets']['doc_count']
        
        ntp_count = results['aggregations']['ntp_packets']['doc_count']  # Commented out
        
        # Convert the last_run datetime to a Unix timestamp (seconds since the epoch)
        timestamp_unix = int(time.mktime(self.last_run.timetuple()))
        
        # Transform the results to the DEME API format
        transformed_results = [
            {
                "timestamp": str(timestamp_unix),
                "instances": [
                    {
                        "instance": "172.22.1.1",
                        "features": [
                            {
                                "feature": "NTP",
                                "value": ntp_count
                            }
                        ]
                    }
                ]
            }
        ]
        return transformed_results



    def DEME_transformation_multidomain(self, results, row=0, timestamp=None):

        # Template with static instances (edit if needed)
        transformed_results = [{
            "timestamp": "0",
            "instances": [
                {"instance": CNIT_node_ip, "features": [{"feature": "DNS", "value": 0}]},
                {"instance": UPC_node_ip, "features": [{"feature": "DNS", "value": 0}]}
            ]
        }]

        # Static DNS counters (CNIT, UPC) per snapshot
        static_ip_values = [
            [26, 26],
            [26, 27],
            [25, 27],
            [27, 29],
            [30, 33],
            [38, 41],
            [54, 53],
            [68, 68],
            [72, 74],
            [69, 67],
            [53, 54],
            [41, 42],
            [31, 33],
            [28, 29],
            [27, 27]
        ]

        # Static timestamps aligned with the above
        static_timestamps = [
            1752501360,
            1752501480,
            1752501600,
            1752501720,
            1752501840,
            1752501960,
            1752502080,
            1752502200,
            1752502320,
            1752502440,
            1752502560,
            1752502680,
            1752502800,
            1752502920,
            1752503040
        ]

        # Clamp row to valid range
        if not isinstance(row, int):
            try:
                row = int(row)
            except Exception:
                logging.warning("Invalid row argument; defaulting to 0.")
                row = 0

        if row < 0:
            row = 0
        if row >= len(static_ip_values):
            row = len(static_ip_values) - 1

        # Try to populate values from results['aggregations']['requests_per_ip'].buckets if present
        try:
            if isinstance(results, dict) and 'aggregations' in results and 'requests_per_ip' in results['aggregations']:
                buckets = results['aggregations']['requests_per_ip'].get('buckets', [])
                if buckets:
                    for i, instance in enumerate(transformed_results[0]["instances"]):
                        if i < len(buckets):
                            try:
                                instance["features"][0]["value"] = int(buckets[i].get('doc_count', 0))
                            except Exception:
                                instance["features"][0]["value"] = 0
                        else:
                            instance["features"][0]["value"] = 0
                else:
                    logging.info("No buckets found in 'requests_per_ip' aggregation; using static row %d.", row)
                    for i, instance in enumerate(transformed_results[0]["instances"]):
                        if i < len(static_ip_values[row]):
                            instance["features"][0]["value"] = static_ip_values[row][i]
                        else:
                            instance["features"][0]["value"] = 0
            else:
                # No aggregation found, fallback to static values
                logging.info("'requests_per_ip' not found in aggregations; using static row %d.", row)
                for i, instance in enumerate(transformed_results[0]["instances"]):
                    if i < len(static_ip_values[row]):
                        instance["features"][0]["value"] = static_ip_values[row][i]
                    else:
                        instance["features"][0]["value"] = 0
        except Exception as e:
            logging.error("Error processing 'requests_per_ip' aggregation: %s. Using static row %d.", str(e), row)
            for i, instance in enumerate(transformed_results[0]["instances"]):
                if i < len(static_ip_values[row]):
                    instance["features"][0]["value"] = static_ip_values[row][i]
                else:
                    instance["features"][0]["value"] = 0

        # Timestamp selection
        timestamp = None  # Use provided timestamp if any
        try:
            # Prefer explicit timestamp argument
            if timestamp is not None:
                if isinstance(timestamp, datetime):
                    ts_str = str(int(timestamp.timestamp()))
                else:
                    try:
                        ts_str = str(int(timestamp))
                    except Exception:
                        ts_str = str(int(time.time()))
                        logging.warning("Provided timestamp invalid; using current time instead.")
            else:
                # Use static timestamp from table
                ts_str = str(static_timestamps[row])

            transformed_results[0]["timestamp"] = ts_str
            return transformed_results

        except Exception as e:
            logging.error("Error setting timestamp in transformed results: %s", str(e))
            raise

    
    
    
    def HOLO_transformation(self, results, row = 0, timestamp=None):
        if not isinstance(results, dict) or 'aggregations' not in results:
            raise ValueError("Invalid results format. Expected 'aggregations' key in response.")

        # Dummy payload template
        transformed_results = [{
            "timestamp": "1705240560",
            "instances": [
                {"instance": "192.168.130.47", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "192.168.130.103", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "192.168.130.27", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "192.168.130.93", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "192.168.130.133", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "192.168.130.68", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "192.168.130.6", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "192.168.130.96", "features": [{"feature": "NEF", "value": 0}]},
                {"instance": "192.168.130.132", "features": [{"feature": "NEF", "value": 0}]}
            ]
        }]
        
        # The following is a sample of the expected output format:
        static_ip_values = [
            [34, 35, 32, 34, 33, 33, 33, 35, 34],
            [34, 35, 34, 33, 33, 33, 33, 34, 35],
            [33, 35, 33, 34, 35, 33, 35, 35, 35],
            [35, 36, 34, 33, 34, 34, 33, 33, 35],
            [38, 36, 34, 34, 32, 34, 34, 35, 36],
            [46, 35, 34, 33, 35, 34, 34, 37, 33],
            [62, 34, 34, 33, 34, 35, 34, 35, 35],
            [76, 35, 35, 35, 34, 33, 34, 35, 35],
            [80, 35, 34,35 ,35 ,34 ,34 ,35 ,36],
            [77 ,33 ,34 ,33 ,34 ,35 ,34 ,36 ,35],
            [61 ,34 ,35 ,35 ,35 ,35 ,35 ,35 ,36],
            [49 ,35 ,35 ,34 ,34 ,34 ,34 ,35 ,36],
            [39 ,35 ,34 ,34 ,35 ,34 ,34 ,35 ,35],
            [36 ,35 ,34 ,34 ,35 ,36 ,34 ,35 ,37],
            [35 ,35 ,34 ,34 ,34 ,34 ,35 ,36 ,37]
        ]
        
        #if results have values for the IP addresses then use them
        #this is a case where results come from ES query are empty
        # "aggregations": {
        #     "requests_per_ip": {
        #       "doc_count_error_upper_bound": 0,
        #       "sum_other_doc_count": 0,
        #       "buckets": []
        #     }
        #   }
        try:
            if 'requests_per_ip' in results['aggregations']:
                buckets = results['aggregations']['requests_per_ip'].get('buckets', [])
                if buckets:
                    for i, instance in enumerate(transformed_results[0]["instances"]):
                        if i < len(buckets):
                            instance["features"][0]["value"] = buckets[i]['doc_count']
                        else:
                            instance["features"][0]["value"] = 0  # Default to 0 if no bucket available
                else:
                    logging.warning("No buckets found in 'requests_per_ip' aggregation. Using static values.")
                    # Fill the transformed results with static values depending on row value
                    # for i, instance in enumerate(transformed_results[0]["instances"]):
                    #     if row < len(static_ip_values) and i < len(static_ip_values[row]):
                    #         instance["features"][0]["value"] = static_ip_values[row][i]
        except Exception as e:
            logging.error("Error processing 'requests_per_ip' aggregation: %s. Using static values.", str(e))
            # Fill the transformed results with static values depending on row value
            # for i, instance in enumerate(transformed_results[0]["instances"]):
            #     if row < len(static_ip_values) and i < len(static_ip_values[row]):
            #         instance["features"][0]["value"] = static_ip_values[row][i]
        

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
