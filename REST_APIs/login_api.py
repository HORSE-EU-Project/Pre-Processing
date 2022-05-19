import os
from flask import Flask, abort, request
from flask_restful import Resource, Api
import requests
import socket
from marshmallow import Schema, fields
import base64
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import user

class LoginQuerySchema(Schema):
    email = fields.Str(required=True)
    password = fields.Str(required=True)

#Configure Keyrock as the IDM
KEYROCK_CLIENT_ID = os.environ.get("KEYROCK_CLIENT_ID", "bb5f6ea7-61f1-4637-bcc2-912fd2b6f1bd")
KEYROCK_CLIENT_SECRET = os.environ.get("KEYROCK_CLIENT_SECRET", "12eab5b6-f063-417f-83e3-85ed61c45fe9")
KEYROCK_DISCOVERY_URL = (
    "https://cloud-20-nic.8bellsresearch.com:443"
)

app = Flask(__name__)
api = Api(app)
loginSchema = LoginQuerySchema()

class Login(Resource):
    def get(self):
        errors = loginSchema.validate(request.args)
        if errors:
            abort(400, str(errors))
        strg = KEYROCK_CLIENT_ID + ":" + KEYROCK_CLIENT_SECRET
        header={
            "Authorization": "Basic " + str(base64.b64encode(strg.encode('ascii')), 'utf-8'),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        body = "username="+request.args["email"]+"&password="+request.args["password"]+"&grant_type=password"
        r = requests.post(url=KEYROCK_DISCOVERY_URL+"/oauth2/token", headers=header, data=body, verify=False)
        json = r.json()
        return json["access_token"]

api.add_resource(Login, '/login')

if __name__ == '__main__':
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(host=ipV4IP, port=5001)