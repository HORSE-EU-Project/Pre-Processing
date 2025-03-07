#A class for reading the queries from the queries file and managing the queries
import json
import logging
from elastic_query import ElasticQuery
from datetime import datetime

class ES_queries:
    
    def __init__(self, config_path):
        self.config_path = config_path
        self.ES_queries = self.read_config()
        logging.info(f"Loaded {len(self.ES_queries)} queries from config file")
        
    def read_config(self):
        try:
            with open(self.config_path, 'r') as file:
                data = json.load(file)
                return [ElasticQuery(**item) for item in data["rules"]]
        except FileNotFoundError:
            logging.error(f"Config file not found: {self.config_path}")
            return []
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in config file: {self.config_path}")
            return []
        except Exception as e:
            logging.error(f"Error reading config file: {str(e)}")
            return []
        
    def write_config(self):
        try:
            # Convert query objects back to dictionaries
            rules = []
            for query in self.ES_queries:
                rule = {
                    "subscription_id": query.subscription_id,
                    "user_id": query.user_id,
                    "subscription_type": query.subscription_type,
                    "endpoint_url": query.endpoint,
                    "DB_url": query.es_url,
                    "index": query.index,
                    "query": query.query,
                    "query_type": query.query_type,
                    "interval": str(int(query.interval.total_seconds())),
                    "active": 1 if query.active else 0,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                rules.append(rule)
            
            data = {"rules": rules}
            
            with open(self.config_path, 'w') as file:
                json.dump(data, file, indent=4)
            
            logging.info(f"Config file updated with {len(rules)} rules")
            return True
        except Exception as e:
            logging.error(f"Error writing config file: {str(e)}")
            return False

    def add_query(self, query):
        self.ES_queries.append(query)
        return self.write_config()
    
    def remove_query(self, subscription_id):
        # Find the query with the matching subscription_id
        for i, query in enumerate(self.ES_queries):
            if query.subscription_id == subscription_id:
                del self.ES_queries[i]
                return self.write_config()
        logging.warning(f"Query with subscription_id {subscription_id} not found")
        return False
    
    def update_query(self, updated_query):
        # Find the query with the matching subscription_id
        for i, query in enumerate(self.ES_queries):
            if query.subscription_id == updated_query.subscription_id:
                self.ES_queries[i] = updated_query
                return self.write_config()
        logging.warning(f"Query with subscription_id {updated_query.subscription_id} not found")
        return False
        
    def get_query(self, subscription_id):
        # Find the query with the matching subscription_id
        for query in self.ES_queries:
            if query.subscription_id == subscription_id:
                return query
        return None