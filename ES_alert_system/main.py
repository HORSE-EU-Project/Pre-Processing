import json
from datetime import datetime
import time
from elastic_query import ElasticQuery
import threading

class ConfigReader:
    @staticmethod
    def read_config(config_file):
        with open(config_file, 'r') as file:
            data = json.load(file)
            return [ElasticQuery(**item) for item in data["queries"]]

def schedule_query(query):
    while True:
        if not query.last_run or datetime.now() >= query.last_run + query.interval:
            results = query.run_query()
            query.post_results(results)
        time.sleep(query.interval.total_seconds())

def main():
    queries = ConfigReader.read_config('config.json')
    threads = []
    for query in queries:
        t = threading.Thread(target=schedule_query, args=(query,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
