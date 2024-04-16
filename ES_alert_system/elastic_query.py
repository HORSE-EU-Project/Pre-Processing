import requests
from datetime import datetime, timedelta

class ElasticQuery:
    def __init__(self, entity_type, es_url, query, endpoint, interval=10, *args, **kwargs):
        self.entity_type = entity_type
        self.es_url = es_url
        self.query = query
        self.endpoint = endpoint
        self.interval = timedelta(seconds=interval)
        self.last_run = None

    def run_query(self):
        headers = {'Content-Type': 'application/json'}
        response = requests.get(f"{self.es_url}/_search", headers=headers, json=self.query)
        self.last_run = datetime.now()
        return response.json()

    def post_results(self, results):
        headers = {'Content-Type': 'application/json'}
        print(results)
        response = requests.post(self.endpoint, headers=headers, json=results)
        return response.status_code

    def print_results(self, results):
        print(results)