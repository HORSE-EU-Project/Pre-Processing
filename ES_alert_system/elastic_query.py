import json
import requests
import logging
from datetime import datetime, timedelta
import DEMO_functions as fun

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#thoughts excerpt
class ElasticQuery:
    def __init__(self, subscription_id, user_id, subscription_type='ES', DB_url='', index='test_index', 
                 query='', headers = {"Content-Type": "application/json"}, endpoint_url='', interval=10, active=True, **kwargs):
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
        
        print("ES URL: ", self.es_url)
        print("Index: ", self.index)
        print("Query: ", self.query)
        print("Headers: ", self.headers)
        print("Endpoint: ", self.endpoint)
        print("Interval: ", self.interval)
        print("Last Run: ", self.last_run)

    def run_query(self):
        #if es_url is "DEME" then read from "a local pcap file" else read from "ES"
        if self.es_url == "DEME":
            return "OK"
        elif self.es_url == "NKUA-DTE":
            #using nkua functions to read from a local pcap file and send the results to the endpoint
            fun.process_capture_in_background("test.pcap")
            return "OK"
        else:
            url = f"{self.es_url}/{self.index}/_search"
            try:
                qry = {"query": self.query}
                


                # If the query is a string, convert it to a dictionary
                key,value = qry["query"].split(":", 1)
                qry["query"] = {key:eval(value.strip())}
                
                logging.info("=========================== Executing query ===========================")
                logging.info("Query: %s", str(json.dumps(qry)))
                logging.info("URL: %s", url)
                
                response = requests.post(url, data=json.dumps(qry), headers=self.headers)
                
                if response.status_code == 200:
                    logging.info("=========Query executed successfully=========")
                    return response.json()
                else:
                    logging.error("Failed to execute query with status code %s", response.status_code)
                    return None
            except Exception as e:
                logging.error("=========Failed to execute query=========",str(e))
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

    
    def convert_query_string(input_string):
        try :
            # Strip leading and trailing spaces and remove the initial "query:" part
            json_part = input_string.split("query:", 1)[1].strip()

            # Properly format the string for JSON conversion by replacing single quotes if necessary
            json_part = json_part.replace('\'', '\"')

            # Convert the string to a dictionary
            query_dict = json.loads(json_part)

            # Create the final dictionary expected
            result = {"query": query_dict}

            # Return the result as a JSON string for clarity and to match the expected output format
            return json.dumps(result)
        
        except Exception as e:
            # Handle exceptions that may arise from incorrect formatting or parsing
            return str(e)
        
    def execute_DEME(self):
        # Read from a local pcap file
        logging.info("Reading from DEME")
        response_json = fun.read_pcap_for_DEME("test.pcap")
        fun.send_data_to_DEME(response_json)
        return None
    
    def execute_NKUA_DTE(self):
        logging.info("Reading from NKUA-DTE")
        
        # use nkua functions to read from a local pcap file
        message_counts = fun.count_pfcp_messages("test.pcap")
        
        #send the message counts to the endpoint
        fun.send_to_bentoml(message_counts)
        
        return None