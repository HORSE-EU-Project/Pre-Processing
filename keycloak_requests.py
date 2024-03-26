from flask_login import current_user
import requests
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

KEYCLOAK_TOKEN_URL="http://10.10.10.14:8080/auth/realms/DFF/protocol/openid-connect/token"
KEYCLOAK_USERINFO_URL="http://10.10.10.14:8080/auth/realms/DFF/protocol/openid-connect/userinfo"
KEYCLOAK_CREDENTIALS_URL="http://10.10.10.14:8080/auth/realms/DFF/account/credentials/password"
#SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET")
SECRET = os.urandom(24)

#Define retry strategy and http adapter for requests
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

def get_kc_token(username, password):
    header={
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": "dff-oidc",
        "client_secret": SECRET,
        "username": username,
        "password": password,
        "grant_type": "password"
    }
    r = http.post(url=KEYCLOAK_TOKEN_URL, headers=header, data=data, verify=False)
    return r

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