from flask import Flask, render_template, request, redirect, url_for, Blueprint, flash
from bokeh.plotting import figure, show, output_file, output_notebook
from bokeh.palettes import Spectral11, colorblind, Inferno, BuGn, brewer
from bokeh.models import HoverTool, value, LabelSet, Legend, ColumnDataSource,LinearColorMapper,BasicTicker, PrintfTickFormatter, ColorBar, DatetimeTickFormatter
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
#from app import app

consumer = Blueprint('consumer', __name__, template_folder='templates')
#consumer.register_blueprint(app)

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
    timestamp_data = []
    '''for i in range(length):
        temp = payload["index"][i].replace('T', ' ')
        timestamp_data.append(re.findall('(.*?)(?=\+)', temp)[0])'''

    '''for t in timestamp_data:
        print(t)'''
    #print(timestamp_data)
    timestamp = []
    for i in range(length):
        timestamp.append(re.findall('(?<=T)(.*?)(?=\+)', payload["index"][i])[0])
    print(timestamp) #x
    values = payload["values"] #y
    #print(values)
    output_file('plot_results.html')
    # create a new plot with a datetime axis type
    TOOLS = "hover,save,pan,box_zoom,reset,wheel_zoom,tap"
    
    p = figure(width=800, height=250, x_axis_type="datetime", title="Last 10 Jetson measurements",
    tools=TOOLS,
    toolbar_location='above')
    
    p.select_one(HoverTool).tooltips = [
        ('timestamp', '@x'),
        ('measurement', '@y')]

    ex = [1,2,3,4,5,6,7,8,9,10]
    p.line(timestamp, values, color='navy', alpha=0.5)
    p.xaxis.formatter = DatetimeTickFormatter(hours="%H:%M:%S", minutes="%H:%M:%S", seconds="%H:%M:%S")

    show(p)

    return render_template('plot_results.html')