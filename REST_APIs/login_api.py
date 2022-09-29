import os
import flask.scaffold
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask import abort, request, Flask
from flask_restx import Api, Resource, reqparse
import marshmallow
import socket
from marshmallow import Schema
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from keycloak_requests import get_kc_token

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

@api.route('/login')
class Login(Resource):
    @api.doc(parser=parser)
    def get(self):
        errors = loginSchema.validate(request.args)
        if errors:
            abort(400, str(errors))
        username = request.args["username"]
        password = request.args["password"]
        token = get_kc_token(username, password)
        if token[0] == None:
            abort(401)
        elif token[0] == 0:
            abort(500)
        return [token[0], token[1], token[2]], 200

if __name__ == '__main__':
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(host=ipV4IP, port=5006)