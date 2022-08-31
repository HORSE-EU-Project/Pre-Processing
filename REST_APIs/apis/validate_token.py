import requests

def validateToken(token, url):
    header={
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "access_token": token,
    }
    r = requests.post(url=url, headers=header, data=data)
    return r