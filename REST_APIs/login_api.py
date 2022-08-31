import os
import flask.scaffold
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask import abort, request, Flask
from flask_restx import Api, Resource, reqparse
import requests
import marshmallow
import socket
from marshmallow import Schema
import sys
import os

SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET")

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)
api = Api(app)

class LoginQuerySchema(Schema):
    username = marshmallow.fields.String(required=True)
    password = marshmallow.fields.String(required=True)
    
loginSchema = LoginQuerySchema()

parser = reqparse.RequestParser()
parser.add_argument('username', location='args', help='The username of your Keycloak user.', required=True)
parser.add_argument('password', location='args', help='The password of your Keycloak user.', required=True)

KEYCLOAK_DISCOVERY_URL="https://dff.8bellsresearch.com:40446/auth/realms/master/protocol/openid-connect/token"

@api.route('/login')
class Login(Resource):
    @api.doc(parser=parser)
    def get(self):
        errors = loginSchema.validate(request.args)
        if errors:
            abort(400, str(errors))
        header={
            "Content-Type": "application/x-www-form-urlencoded",
        }
        username = request.args["username"]
        password = request.args["password"]
        data = {
            "client_id": "dff-oidc",
            "client_secret": SECRET,
            "username": username,
            "password": password,
            "grant_type": "password"
        }
        r = requests.post(url=KEYCLOAK_DISCOVERY_URL, headers=header, data=data, verify=False)
        json = r.json()
        token = json["access_token"]
        return token

if __name__ == '__main__':
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(host=ipV4IP, port=5001)