import requests
from datetime import datetime, timedelta

class ElasticQuery:
    def __init__(self, es_url, query, endpoint, interval_minutes=1):
        self.es_url = es_url
        self.query = query
        self.endpoint = endpoint
        self.interval = timedelta(minutes=interval_minutes)
        self.last_run = None

    def run_query(self):
        headers = {'Content-Type': 'application/json'}
        response = requests.get(f"{self.es_url}/_search", headers=headers, json=self.query)
        self.last_run = datetime.now()
        return response.json()

    def post_results(self, results):
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.endpoint, headers=headers, json=results)
        return response.status_code
