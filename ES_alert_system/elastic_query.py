import requests
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch

class ElasticQuery:
    def __init__(self, entity_type, es_url, query, endpoint, interval=10, *args, **kwargs):
        self.es = Elasticsearch([es_url])
        self.query = query
        self.endpoint = endpoint
        self.headers = headers
        self.interval = timedelta(seconds=interval)
        self.last_run = None

    def run_query(self):
        return self.es.search(index="test_index", body=self.query)

    def post_results(self, results):
        response = requests.post(self.endpoint, json=results, headers=self.headers)
        return response.status_code

    def print_results(self, results):
        print(results)