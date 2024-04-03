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
            store_dff_data_in_csv(dff_data)
            return {"message": "I received you data!"}, 200
        else:
            print("Data not in json format.") 
            return {"message": "Data not in json format."}, 400

api.add_resource(ReceiveDFF, '/dff-data')

def store_data_in_csv(json_data):
    # Assuming json_data is a dictionary that has been parsed from a JSON payload
    # For example: json_data = {"data": [{"type": "X", "value": "example data"}]}

    # Extract the "type" from the first item in the "data" list as the file name
    file_name = json_data["data"][0]["type"] + ".csv"

    # Define the folder path
    folder_path = "./subscription_data"
    file_path = os.path.join(folder_path, file_name)

    # Ensure the folder exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Convert the JSON data to a pandas DataFrame
    df = pd.DataFrame(json_data["data"])

    # Check if the CSV file already exists
    if os.path.isfile(file_path):
        # If it exists, append without writing the header
        df.to_csv(file_path, mode='a', header=False, index=False)
    else:
        # If it does not exist, write with the header
        df.to_csv(file_path, mode='w', header=True, index=False)

    print(f"Data stored in {file_path}")


if __name__ == '__main__':
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(host="0.0.0.0")