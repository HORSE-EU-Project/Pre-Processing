import os
import flask.scaffold
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask import abort, request, Flask
from flask_restx import Api, Resource, reqparse
import requests
import marshmallow
import socket
from marshmallow import Schema, validate
import base64
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import user

#Configure Keyrock as the IDM
KEYROCK_CLIENT_ID = os.environ.get("KEYROCK_CLIENT_ID")
KEYROCK_CLIENT_SECRET = os.environ.get("KEYROCK_CLIENT_SECRET")
KEYROCK_DISCOVERY_URL = os.environ.get("KEYROCK_DISCOVERY_URL")
SQLITE_DB_URL = os.environ.get("SQLITE_URL") or None

app = Flask(__name__)
api = Api(app)

class LoginQuerySchema(Schema):
    email = marshmallow.fields.Email(required=True)
    password = marshmallow.fields.String(required=True)
    
loginSchema = LoginQuerySchema()

parser = reqparse.RequestParser()
parser.add_argument('email', location='args', help='The email that you used when you signed up in Keyrock IDM.', required=True)
parser.add_argument('password', location='args', help='The password that you used when you signed up in Keyrock IDM.', required=True)

@api.route('/login')
class Login(Resource):
    @api.doc(parser=parser)
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
        email = request.args["email"]
        body = "username="+email+"&password="+request.args["password"]+"&grant_type=password"
        r = requests.post(url=KEYROCK_DISCOVERY_URL+"/oauth2/token", headers=header, data=body, verify=False)
        json = r.json()
        token = json["access_token"]
        #print(r, r.status_code, token)
        #user.User.update_field("email", email, "user", "token", token, path = SQLITE_DB_URL)
        return token

if __name__ == '__main__':
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(host=ipV4IP, port=5001)