from flask import Flask
import flask.scaffold
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from apis import api
import socket
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)

# swagger specific configuration
SWAGGER_URL = '/apis/doc'
API_URL = 'REST_APIs/static/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "DFF REST APIs"
    }
)

app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

api.init_app(app)

if __name__ == '__main__':
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(host=ipV4IP, port=5007)