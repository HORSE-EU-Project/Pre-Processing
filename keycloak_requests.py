import requests
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

KEYCLOAK_TOKEN_URL="http://10.10.10.13:8080/auth/realms/DFF/protocol/openid-connect/token"
KEYCLOAK_USERINFO_URL="http://localhost:8080/auth/realms/DFF/protocol/openid-connect/userinfo"
SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET")

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
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
    }
    r= http.get(KEYCLOAK_USERINFO_URL, headers=headers, data=payload)
    return r