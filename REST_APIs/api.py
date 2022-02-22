from flask import Flask, abort, request
from flask_restful import Resource, Api
import requests
import socket
from marshmallow import Schema, fields

# class LoginQuerySchema(Schema):
#     username = fields.Str(required=True)
#     password = fields.Str(required=True)

class DataPerIndexQuerySchema(Schema):
    type = fields.Str(required=True)

# Configure Keyrock as the IDM
# KEYROCK_CLIENT_ID = os.environ.get("KEYROCK_CLIENT_ID", "bb5f6ea7-61f1-4637-bcc2-912fd2b6f1bd")
# KEYROCK_CLIENT_SECRET = os.environ.get("KEYROCK_CLIENT_SECRET", "12eab5b6-f063-417f-83e3-85ed61c45fe9")
# KEYROCK_DISCOVERY_URL = (
#     #"https://account.lab.fiware.org"
#     "https://cloud-20-nic.8bellsresearch.com:443"
# )

app = Flask(__name__)
api = Api(app)
#loginSchema = LoginQuerySchema()
getDataSchema = DataPerIndexQuerySchema()

# class Login(Resource):
#     def get(self):
#         errors = loginSchema.validate(request.args)
#         if errors:
#             abort(400, str(errors))
#         strg = KEYROCK_CLIENT_ID + ":" + KEYROCK_CLIENT_SECRET
#         header={
#             "Authorization": "Basic " + str(base64.b64encode(strg.encode('ascii')), 'utf-8'),
#             "Content-Type": "application/x-www-form-urlencoded",
#             "Accept": "application/json"
#         }
#         body = "username="+request.args["username"]+"&password="+request.args["password"]+"&grant_type=password"
#         r = requests.post(url=KEYROCK_DISCOVERY_URL+"/oauth2/token", headers=header, data=body, verify=False)
#         json = r.json()
#         return json["access_token"]

# api.add_resource(Login, '/api-login')

class GetTypeDataPerTimeIndex(Resource):
    def get(self):
        errors = getDataSchema.validate(request.args)
        if errors:
            abort(400, str(errors))
        header={
            "Content-Type": "application/json"
        }
        table = "et" + (request.args["type"]).lower()
        body = "{\"stmt\":\"SELECT * FROM doc." + table + " ORDER BY time_index;\"}"
        print(body)
        r = requests.post(url="http://10.0.18.77:4200/_sql", headers=header, data=body, verify=False)
        data = r.json()
        entities = []
        for row in data["rows"]:
            new_data_dict = {}
            new_data_dict["attributes"] = []
            for i in range(0, len(row)):
                column = data["cols"][i]
                if column != "fiware_servicepath" and column != "__original_ngsi_entity__":
                    if i<5:
                        new_data_dict[data["cols"][i]] = row[i]
                    else:
                        (new_data_dict["attributes"]).append({"attrName": data["cols"][i], "value": row[i]})
            entities.append(new_data_dict)
        return entities

api.add_resource(GetTypeDataPerTimeIndex, '/getTypeDataPerTimeIndex')


if __name__ == '__main__':
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(host=ipV4IP, port=5001)