from flask import Flask, request
from flask_restful import Resource, Api
import socket

app = Flask(__name__)
api = Api(app)

class ReceiveDFF(Resource):
    def post(self):
        dff_data = request.get_json()
        if isinstance(dff_data, dict):
            print("I received your data!")
            print(dff_data)
            return {"message": "I received you data!"}, 200
        else:
            print("Data not in json format.") 
            return {"message": "Data not in json format."}, 400

api.add_resource(ReceiveDFF, '/dff-data')


if __name__ == '__main__':
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(host="0.0.0.0")