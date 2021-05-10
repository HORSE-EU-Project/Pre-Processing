# DFF
Master Repository of DFF Mechanism


# Authentication Branch
Flask is used for developing the web application.
First, you’ll need to install those third-party dependencies mentioned above. 
You’ll do this by installing the contents of the requirements.txt file:

pip install -r requirements.txt

Then, set the environmental variables containing the CLIENT_ID and CLIENT_SECRET of the app, as produced from Keyrock IDM when registering your app.

set KEYROCK_CLIENT_ID=your_client_id 

set KEYROCK_CLIENT_SECRET=your_client_secret

Note: Alternatively, you could paste the strings directly here and store them in these variables. However, the client secret should not be shared or committed to any public repository. In other words, be very careful not to check in this file if you paste your real client credentials in here.

Now, you are ready to run the app (in a virtual environment in Visual Studio Code simply run the following):

py app.py
