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
from flask_swagger_ui import get_swaggerui_blueprint

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from keycloak_requests import get_kc_token

SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET")

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)

# swagger specific configuration
# SWAGGER_URL = '/login'
# API_URL = '/login/doc/static/swagger-login.json'
# SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
#     SWAGGER_URL,
#     API_URL,
#     config={
#         'app_name': "DFF Login REST API"
#     }
# )

# app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

api = Api(app)

api = Api(
    title='DFF Login REST API',
    version='1.0',
    description='This is the DFF Login REST API.'
)

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
        response = get_kc_token(username, password)
        if response.status_code != 200:
            abort(response.status_code)
        token = response.json()["access_token"]
        return token, 200

if __name__ == '__main__':
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(host=ipV4IP, port=5006)