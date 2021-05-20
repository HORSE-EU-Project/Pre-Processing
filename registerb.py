from io import StringIO
from logging import exception
from flask import Flask, render_template, request, redirect, url_for , jsonify, flash, Blueprint, current_app
import os
from os.path import join, dirname, realpath
#from requests.api import head
#from requests.models import HTTPError
from werkzeug.datastructures import Headers
from werkzeug.utils import secure_filename
import socket
#import fi
import re
import requests

registerb = Blueprint('registerb', __name__, template_folder='templates')

#Allowed files check
ALLOWED_EXTENSIONS = {'json','txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@registerb.route("/register", methods= ['GET', 'POST'])
def register():
    if request.method == 'POST':
        if 'uploadedJson' not in request.files:
            #flash('Please upload your file','error')
            return redirect(request.url)
        file = request.files['uploadedJson']
        if file.filename == '':
            flash('The name of the file is no defined','error')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            #parsing the file & making the request
            flash('File uploaded successfully','success')
            registerDevice(filename)
            return redirect(request.url)    
        else:
            flash('Incorrect file is uploaded','error')
            return redirect(request.url)    
    else:
        return render_template('register.html')

#Parsing the uploaded registration file
def registerDevice(filename):
    with open('static/json/' + filename, 'r') as file:
        fileContents = file.read().replace(' ', '')
        #Get url
        httpPattern = r'h.*devices'
        try:
            matchPostURL = re.search(httpPattern, fileContents).group()
            #print(matchPostURL)
        except AttributeError:
            print('Couldn\'t find the url')
            flash('Error getting url','error')
            matchPostURL = re.search(httpPattern, fileContents)
        #Get headers!
        headersPattern = r'(?<=\')[\w:/-]+(?=\')'
        try:
            matchHeaders = re.findall(headersPattern, fileContents)
            #print(matchHeaders)
        except AttributeError:
            print('error Headers')
            flash('Error getting headers','error')
        #Creating dict of headers
        headersDict = {}
        for item in matchHeaders:
            a = item.split(':')
            headersDict[a[0]] = a[1]
        #print(headersDict)
            
        #Returnpayload
        payloadPattern =r'(?<=\')\{[\w\W\s\S\d\D]+\}(?=(\s)*\')'
        try:
            matchPayload = re.search(payloadPattern, fileContents).group()
            #print(matchPayload)
        except AttributeError:
            print('error Payload')
            flash('Error getting correct payload','error') 
        #print(matchPayload)
        sendRequestToFiware(matchPostURL,headersDict,matchPayload)
        
#Sending a request to fiware       
def sendRequestToFiware(matchPostURL,headersDict,matchPayload):
    #print(headersDict)
    try:
        r = requests.post(matchPostURL,headers = headersDict,data= matchPayload)
        if r.status_code == 201:
            flash('Device registered successfully','success')
        elif r.status_code == 409:
            flash('Device has already been registered','info')
        #print(r.status_code)
    except requests.exceptions.RequestException as e: 
        flash('Internal error')
        raise SystemExit(e)