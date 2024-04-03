from flask import Flask, request
from flask_restful import Resource, Api
import socket
import csv
import os

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
    # Check if 'type' key exists in the data
    if 'type' not in dff_data:
        print("The data does not contain a 'type' field.")
        return

    # Prepare the directory path
    dir_path = './subscription_data'
    os.makedirs(dir_path, exist_ok=True)

    # Prepare the file path
    file_name = f"{dff_data['type']}.csv"
    file_path = os.path.join(dir_path, file_name)

    # Determine if the file exists to choose write mode
    write_mode = 'a' if os.path.exists(file_path) else 'w'

    # Define CSV headers based on dff_data keys
    headers = list(dff_data.keys())

    with open(file_path, mode=write_mode, newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        
        # Write header only if creating the file new
        if write_mode == 'w':
            writer.writeheader()
        
        writer.writerow(dff_data)

    print(f"Data successfully stored in {file_path}")



if __name__ == '__main__':
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(host="0.0.0.0")