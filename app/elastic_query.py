import json
import requests
import logging
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv
load_dotenv()

# Set up logging without timestamps for cleaner container logs
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

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
        
        # For static mode: track current row index in demo_10_apiEXP_values.json
        self.static_data_index = 0
        self.static_data_cache = None
        self.static_data_metadata = None
        
        # Logging the initialized values
        logging.info(f"ES URL: {self.es_url}")
        logging.info(f"Index: {self.index}")
        logging.info(f"Query: {self.query}")
        logging.info(f"Headers: {self.headers}")
        logging.info(f"Endpoint: {self.endpoint}")
        logging.info(f"Interval: {self.interval}")

    def run_query(self, current_time=None, use_current_time=False):
        url = f"{self.es_url}/{self.index}/{self.query_type}"

        # If current_time is provided (iteration mode), use it
        if current_time is not None:
            now = current_time
        elif use_current_time:
            # In continuous mode with no time range specified, always use current time
            now = datetime.now()
        else:
            # Otherwise use ES_DATA_END_TIME or current time (backward compatibility)
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

                    #logging.info("From time: %s", self.previous_last_run)
                    #logging.info("To time: %s", self.last_run)
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

    def run_query_static(self):
        """
        Reads and returns results from a static JSON file (demo_10_apiEXP_values.json)
        instead of querying Elasticsearch. Used for demo/testing purposes.
        Iterates through the data rows on each call.
        """
        try:
            # Path to the demo values JSON file
            demo_filename = os.getenv('STATIC_DATA_FILE_PATH', 'static_data_config/demo_10_apiEXP_values.json')
            demo_file_path = os.path.join(os.path.dirname(__file__), demo_filename)
            
            # Load the file if not already cached
            if self.static_data_cache is None:
                logging.info("=========================== Loading st. data file ===========================")
                #logging.info("Reading from file: %s", demo_file_path)
                
                with open(demo_file_path, 'r') as f:
                    self.static_data_cache = json.load(f)
                
                if 'data' not in self.static_data_cache or not isinstance(self.static_data_cache['data'], list):
                    logging.error("Invalid format in demo_10_apiEXP_values.json: expected 'data' array")
                    return None
                
                # Load metadata from the JSON file
                self.static_data_metadata = self.static_data_cache.get('metadata', {
                    'feature_name': 'NTP',
                    'value_type': 'float',
                    'timestamp_format': 'unix'
                })
                logging.info("Loaded metadata: %s", self.static_data_metadata)
                #logging.info("Loaded %d data rows from demo_10_apiEXP_values.json", len(self.static_data_cache['data']))
            
            # Get the current row
            data_rows = self.static_data_cache['data']
            if not data_rows:
                logging.error("No data rows found in demo_10_apiEXP_values.json")
                return None
            
            # Get current row (with wraparound)
            current_row = data_rows[self.static_data_index % len(data_rows)]
            
            logging.info("=========================== Reading st. data ===========================")
            #logging.info("Timestamp: %s", current_row.get('timestamp'))
            
            # Convert the row data to Elasticsearch aggregation format
            buckets = []
            for ip, count in current_row.get('values', {}).items():
                buckets.append({
                    "key": ip,
                    "doc_count": count
                })
            
            results = {
                "aggregations": {
                    "requests_per_ip": {
                        "buckets": buckets
                    }
                }
            }
            
            # Set time window for logging purposes
            now = datetime.now()
            self.previous_last_run = now - self.interval
            self.last_run = now
            
            logging.info("=========St. data loaded successfully=========")
            #logging.info("From time: %s", self.previous_last_run)
            #logging.info("To time: %s", self.last_run)
            logging.info("Requests per IP:")
            
            for bucket in buckets:
                ip = bucket.get('key')
                count = bucket.get('doc_count')
                logging.info("IP: %s - Count: %d", ip, count)
            
            logging.info("=============================================================")
            
            # Advance to next row for next call
            self.static_data_index += 1
            
            # Optional: loop back to start when reaching the end
            if self.static_data_index >= len(data_rows):
                logging.info("Reached end of st. data, looping back to start")
                self.static_data_index = 0
            
            return results
            
        except FileNotFoundError:
            logging.error("demo_10_apiEXP_values.json file not found at %s", demo_file_path)
            return None
        except json.JSONDecodeError as jde:
            logging.error("Invalid JSON in demo_10_apiEXP_values.json: %s", str(jde), exc_info=True)
            return None
        except Exception as e:
            logging.error("Error reading st. data: %s", str(e), exc_info=True)
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
                response = requests.post(self.endpoint, json=transformed_results, headers=self.headers)
                
                # # save a fake successful response code for return
                # class FakeResponse:
                #     status_code = 200
                
                # response = FakeResponse()
                
                
                
                
                if response.status_code == 200:
                    logging.info("Results successfully posted to DEME API.")
                else:
                    logging.warning("Failed to post results to DEME API: HTTP %s", response.status_code)

                

                return response.status_code
            except Exception as e:
                logging.warning("=========posting results=========")
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
        
        # Load demo file to get metadata and IPs dynamically
        demo_filename = os.getenv('STATIC_DATA_FILE_PATH', 'static_data_config/demo_10_apiEXP_values.json')
        demo_file_path = os.path.join(os.path.dirname(__file__), demo_filename)
        
        # Default metadata if not found
        metadata = {
            'feature_name': 'NTP',
            'value_type': 'float',
            'timestamp_format': 'unix'
        }
        
        try:
            with open(demo_file_path, 'r') as f:
                demo_data = json.load(f)
            
            # Load metadata from JSON file
            if 'metadata' in demo_data:
                metadata.update(demo_data['metadata'])
                logging.info("Using metadata from JSON: %s", metadata)
            else:
                logging.warning("No metadata found in JSON, using defaults: %s", metadata)
            
            # Extract all unique IPs from the demo data
            unique_ips = set()
            if 'data' in demo_data and isinstance(demo_data['data'], list):
                for row in demo_data['data']:
                    if 'values' in row and isinstance(row['values'], dict):
                        unique_ips.update(row['values'].keys())
            
            # Sort IPs for consistent ordering
            sorted_ips = sorted(unique_ips)
            
            # Build instances array dynamically using metadata
            feature_name = metadata.get('feature_name', 'NTP')
            value_type = metadata.get('value_type', 'float')
            
            # Initialize value based on type
            if value_type == 'float':
                initial_value = 0.0
            elif value_type == 'int':
                initial_value = 0
            else:
                initial_value = 0.0
            
            instances = []
            for ip in sorted_ips:
                instances.append({
                    "instance": ip,
                    "features": [{"feature": feature_name, "value": initial_value}]
                })
            
            logging.info("Initialized %d instances with feature '%s' (type: %s)", len(instances), feature_name, value_type)
            
        except FileNotFoundError:
            logging.warning("Demo file not found at %s, using empty instances", demo_file_path)
            instances = []
            feature_name = metadata['feature_name']
            value_type = metadata['value_type']
        except Exception as e:
            logging.error("Error loading demo file for instances: %s", str(e))
            instances = []
            feature_name = metadata['feature_name']
            value_type = metadata['value_type']
        
        transformed_results = [{
            "timestamp": "1705240560",
            "instances": instances
        }]       

        requests_per_ip = results['aggregations'].get('requests_per_ip', {}).get('buckets', [])

        # Build a mapping from IP to doc_count
        ip_counts = {bucket.get('key'): bucket.get('doc_count') for bucket in requests_per_ip}

        # Overwrite the feature value if the IP matches (using metadata-driven feature name)
        for instance in transformed_results[0]["instances"]:
            ip = instance["instance"]
            if ip in ip_counts:
                for feature in instance["features"]:
                    if feature["feature"] == feature_name:
                        # Apply value type conversion based on metadata
                        if value_type == 'float':
                            feature["value"] = float(ip_counts[ip])
                        elif value_type == 'int':
                            feature["value"] = int(ip_counts[ip])
                        else:
                            feature["value"] = float(ip_counts[ip])

        # Set timestamp based on metadata format
        try:
            timestamp_format = metadata.get('timestamp_format', 'unix')
            
            if timestamp is None:
                if timestamp_format == 'unix':
                    timestamp = str(int(time.mktime(self.last_run.timetuple())))
                elif timestamp_format == 'iso':
                    timestamp = self.last_run.isoformat()
                else:
                    timestamp = str(int(time.mktime(self.last_run.timetuple())))
            elif isinstance(timestamp, datetime):
                if timestamp_format == 'unix':
                    timestamp = str(int(time.mktime(timestamp.timetuple())))
                elif timestamp_format == 'iso':
                    timestamp = timestamp.isoformat()
                else:
                    timestamp = str(int(time.mktime(timestamp.timetuple())))
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
