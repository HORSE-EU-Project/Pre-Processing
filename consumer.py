from types import MethodType
from flask import Flask, render_template, request, redirect, url_for, Blueprint, flash
import os
from flask.globals import current_app
import requests
import json
import re
import datetime
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
    UserMixin
)
import plotly.express as px
import plotly
import pandas as pd

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
    x = requests.get('http://10.0.20.226:8668/v2/entities/urn:ngsi-ld:jetson/attrs/eco2name?lastN=10', headers = {'Accept': 'text/plain', 'Fiware-Service': 'myOpenIoT', 'Fiware-ServicePath': '/'}, data = '')
    print(x.status_code)
    if x.status_code != 200:
        flash("Request was not succesfully executed.")
        return redirect(url_for('index'))
    #print(x.text)
    payload=json.loads(x.text)
    #print(payload)
    length = len(payload["index"])
    timestamp = []
    for i in range(length):
        temp = payload["index"][i].replace('T', ' ')
        timestamp.append(re.findall('(.*?)(?=\+)', temp)[0])
    
    '''timestamp = []
    for i in range(length):
        timestamp.append(re.findall('(?<=T)(.*?)(?=\+)', payload["index"][i])[0])'''

    #print(timestamp) #x
    values = payload["values"] #y
    #print(values)

    #create a pandas DataFrame
    data_tuples = list(zip(timestamp,values))
    data = pd.DataFrame(data_tuples, columns=['timestamp', 'value'])
    #print(data)
    data['timestamp'] = pd.to_datetime(data['timestamp'], format='%Y-%m-%d %H:%M:%S')
    print(data)
    
    fig = px.line(data, x='timestamp', y="value")
    
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template("plot_results.html", graphJSON=graphJSON)

@consumer.route('/plate')
def show_plate_num():
    x = requests.get('http://10.0.20.226:1026/v2/entities/plateDetectedIdxxx?options=keyValues')
    print(x.status_code)
    if x.status_code != 200:
        flash("Request was not succesfully executed.")
        return redirect(url_for('index'))
    payload=json.loads(x.text)
    num = payload["plate"][2:]
    return render_template("show_plate_num.html", number=num)
