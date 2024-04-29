#A class for reading the queries from the queries file and managing the queries

class ES_queries():
    
    def __init__(self, ES_URL):
        self.ES_URL = ES_URL
        self.ES_queries = self.read_config()
        
    
    def read_config(self):
        with open(self.ES_URL, 'r') as file:
            data = json.load(file)
            return [ElasticQuery(**item) for item in data["rules"]]
        
    def write_config(self):
        with open(self.rules, 'w') as file:
            json.dump(data, file, indent=4)

    def add_query(self, query):
        self.ES_queries.append(query)
        write_config()
    
    def remove_query(self, query):
        self.ES_queries.remove(query)
        write_config()
    
    def update_query(self, query):
        self.ES_queries[self.ES_queries.index(query)] = query
        write_config()