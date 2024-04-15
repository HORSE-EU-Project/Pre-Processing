from flask import Flask, request
from flask_restful import Resource, Api
import socket
import csv
import os
import pandas as pd
import json

app = Flask(__name__)
api = Api(app)

class ReceiveDFF(Resource):
    def post(self):
        dff_data = request.get_json()
        if isinstance(dff_data, dict):
            print("I received your data!")
            #print(dff_data)
            store_data_in_file(dff_data)
            return {"message": "I received you data!"}, 200
        else:
            print("Data not in json format.") 
            return {"message": "Data not in json format."}, 400

api.add_resource(ReceiveDFF, '/dff-data')

def store_data_in_file(data):
    # Define the directory to store data
    directory = "./subscription_data"
    
    # Ensure the directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Generate a timestamp-based filename to avoid overwriting previous files
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}.json"
    filepath = os.path.join(directory, filename)
    
    # Try to write the data to a file
    try:
        with open(filepath, 'w') as file:
            json.dump(data, file)
        print(f"Data successfully stored in {filepath}")
    except Exception as e:
        # Handle potential errors in file operation
        print(f"Failed to store data: {e}")


if __name__ == '__main__':
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(host="0.0.0.0")