from flask import Flask, render_template, request, redirect, url_for
import os
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename

# Referencing the file __name__

app = Flask(__name__)

# Upload folder
UPLOAD_FOLDER = 'static/json'
#LLOWED_EXTENSIONS = {'json', 'csv'}

app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER

@app.route('/', methods= ["POST", "GET"])

def upload_file():
    if request.method == "POST":
        file1 = request.files["jsonFile"]
        filename = secure_filename(file1.filename)
        file1.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return render_template('displayJson.html')
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
