from flask import Flask, request
from flask_restful import Resource, Api
import socket
import csv
import os
import json

app = Flask(__name__)
api = Api(app)

class ReceiveDFF(Resource):
    def post(self):
        dff_data = request.get_json()
        if isinstance(dff_data, dict):
            print("I received your data!")
            print(dff_data)
            store_dff_data_in_csv(dff_data)
            return {"message": "I received you data!"}, 200
        else:
            print("Data not in json format.") 
            return {"message": "Data not in json format."}, 400

api.add_resource(ReceiveDFF, '/dff-data')

def store_dff_data_in_csv(dff_data):
    # Ensure the subscription_data directory exists
    dir_path = "./subscription_data"
    os.makedirs(dir_path, exist_ok=True)
    
    # Iterate through each item in the 'data' list
    for item in dff_data.get("data", []):
        # Extract the type (X) to name the CSV file
        csv_type = item.get("type")
        if csv_type:
            file_path = os.path.join(dir_path, f"{csv_type}.csv")
            
            # Check if the CSV file needs headers (new file)
            needs_header = not os.path.exists(file_path)
            
            # Open (or create) the CSV file for appending
            with open(file_path, 'a', newline='') as csv_file:
                # Define the CSV column names (keys of the JSON data)
                fieldnames = item.keys()
                
                # Create a DictWriter object with the fieldnames
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                
                # Write header if the file is new
                if needs_header:
                    writer.writeheader()
                
                # Write the JSON data as a row in the CSV
                writer.writerow(item)


if __name__ == '__main__':
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(host="0.0.0.0")