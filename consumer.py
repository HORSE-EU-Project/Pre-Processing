from flask import Flask, render_template, request, redirect, url_for, Blueprint, flash
import os
from flask.globals import current_app
import requests
import json
import re
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
    UserMixin
)

consumer = Blueprint('consumer', __name__, template_folder='templates')

@consumer.route('/consumer')
def consume():
    if current_user.is_authenticated:
        return render_template('consume_data.html')
    else:
        flash('You should login first!')
        return redirect(url_for('index'))

@consumer.route('/request')
def send_request():
    x = requests.get('http://10.0.20.226:8668/v2/entities/hippo/attrs/count?lastN=10', headers = {'Accept': 'text/plain', 'Fiware-Service': 'myOpenIoT', 'Fiware-ServicePath': '/'}, data = '')
    if x.status_code!=200:
        flash("Request was not succesfully executed. Response:", x.text)
        redirect(url_for('index'))
    #print(x.text)
    payload=json.loads(x.text)
    length = len(payload["index"])
    timestamp = []
    for i in range(length):
        timestamp.append(re.findall('(?<=T)(.*?)(?=\+)', payload["index"][i])[0])
    print(timestamp)
    print(payload["values"])
    return render_template('plot_results.html')