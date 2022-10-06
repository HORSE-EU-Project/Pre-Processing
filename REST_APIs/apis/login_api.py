import os
import flask.scaffold
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask import abort, request
from flask_restx import Namespace, Resource, reqparse
import marshmallow
from marshmallow import Schema
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from keycloak_requests import get_kc_token

SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET")

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

api = Namespace('apis/dffData', description='Login API')

class LoginQuerySchema(Schema):
    username = marshmallow.fields.String(required=True)
    password = marshmallow.fields.String(required=True)
    
loginSchema = LoginQuerySchema()

parser = reqparse.RequestParser()
parser.add_argument('username', location='args', help='The username of your Keycloak user.', required=True)
parser.add_argument('password', location='args', help='The password of your Keycloak user.', required=True)

@api.route('')
class Login(Resource):
    @api.doc(parser=parser)
    def get(self):
        errors = loginSchema.validate(request.args)
        if errors:
            abort(400, str(errors))
        username = request.args["username"]
        password = request.args["password"]
        response = get_kc_token(username, password)
        if response.status_code != 200:
            abort(response.status_code)
        token = response.json()["access_token"]
        return token, 200