from flask import Flask
from apis import api
import socket

app = Flask(__name__)

api.init_app(app)

if __name__ == '__main__':
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(host=ipV4IP, port=5003)