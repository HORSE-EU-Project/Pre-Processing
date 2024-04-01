from flask import Flask, render_template, request, redirect, Blueprint, flash, url_for, session
from flask_login import current_user
import requests
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

#KEYCLOAK_TOKEN_URL="http://10.10.10.14:8080/auth/realms/DFF/protocol/openid-connect/token"
#KEYCLOAK_USERINFO_URL="http://10.10.10.14:8080/auth/realms/DFF/protocol/openid-connect/userinfo"
#KEYCLOAK_CREDENTIALS_URL="http://10.10.10.14:8080/auth/realms/DFF/account/credentials/password"
#SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET")

# Corrected Token URL
KEYCLOAK_TOKEN_URL = "http://10.10.10.14:8080/realms/DFF/protocol/openid-connect/token"

# Corrected Userinfo URL
KEYCLOAK_USERINFO_URL = "http://10.10.10.14:8080/realms/DFF/protocol/openid-connect/userinfo"

#KEYCLOAK_CREDENTIALS_URL="http://10.10.10.14:8080/realms/DFF/protocol/openid-connect/auth/password"

SECRET = os.getenv('KEYCLOAK_CLIENT_SECRET_KEY')

SECRET = "kp17oYqbZdWoPn4b5XrI4bDWj0vSbndA"

print("Secret Key keycloak request: ", SECRET)

#Define retry strategy and http adapter for requests
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

def get_kc_token(username, password):
    print("================================111111111=============================")
    header={
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": "account",
        "client_secret": SECRET,
        "username": username,
        "password": password,
        "grant_type": "password"
    }
    try:
        print("================================22222=============================")
        response = http.post(url=KEYCLOAK_TOKEN_URL, headers=header, data=data, verify=True)  # Consider your SSL strategy
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")  # or log this
    except Exception as err:
        print(f"An error occurred: {err}")  # or log this

def get_kc_userinfo(token):
    payload={}
    headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer {}".format(token)
    }
    r = http.get(KEYCLOAK_USERINFO_URL, headers=headers, data=payload)
    return r

def change_password(currentPassword, newPassword, confirmation):
    payload = {
        "currentPassword": currentPassword,
        "newPassword": newPassword,
        "confirmation": confirmation
    }
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer {}".format(current_user.token),
        "Content-Type": "application/json"
    }
    r = http.post(url=KEYCLOAK_CREDENTIALS_URL, headers=headers, data=payload, verify=False)
    return r
