import requests
import json

url = "http://dff.8bellsresearch.com/apis/subscriptions"

payload = json.dumps({
  "description": "Notify Me",
  "subject": {
    "entities": [
      {
        "idPattern": ".*",
        "type": "test"
      }
    ],
    "condition": {
      "attrs": []
    }
  },
  "notification": {
    "http": {
      "url": "http://test.com"
    },
    "attrs": [],
    "metadata": [
      "dateCreated",
      "dateModified"
    ]
  }
})
headers = {
  'X-Auth-token': 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJhVDdrTVhxWThWZjMxTzNUSXdsVEpVUE5NUmczYmhuVkduZ2I2VXM1Rkp3In0.eyJleHAiOjE2NjQ4NzcxODYsImlhdCI6MTY2NDg3MzU4NiwianRpIjoiODgzODViNjQtOWEzNS00MWYxLTlhNjAtNzQ1MjliODZkNmE5IiwiaXNzIjoiaHR0cDovLzEwLjEwLjEwLjEzOjgwODAvYXV0aC9yZWFsbXMvREZGIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjczYmZhMDc0LWFiN2YtNGI4MS1iYWU1LTk4YTljN2E5ZDE0ZCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImRmZi1vaWRjIiwic2Vzc2lvbl9zdGF0ZSI6ImE0MTA0ZjdjLTY5YTItNDRkZC04MmZkLTQ4YTQzMzU3MjIxMyIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsiZGVmYXVsdC1yb2xlcy1kZmYiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJlbWFpbCBwcm9maWxlIiwic2lkIjoiYTQxMDRmN2MtNjlhMi00NGRkLTgyZmQtNDhhNDMzNTcyMjEzIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJuYW1lIjoiRGVzcGluYSBHa2F0emlvdXJhIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiZGVzcGluYSIsImdpdmVuX25hbWUiOiJEZXNwaW5hIiwiZmFtaWx5X25hbWUiOiJHa2F0emlvdXJhIiwiZW1haWwiOiJkZXBpLmdhdHpAZ21haWwuY29tIn0.kl0GJqCjr2olnM4bVMSfGL9-AxMGsYPQNuU7NX4e_AWjSea52U0eFKEx-yH6OeS7q2E_qws2jgc9OpdgBId_18JFUxOMgDmqHRzux4uh7MnI3RwZBzWFOpiZnoU6m0rhdIapYh9hNXcebby_0eEX_Ula6p9DkUW4S0E5WUYRh5bMgGYKoJUKLnrWtsJ8pgjVRyfBHCNqJEDI-Vs8CwmjZS0qkjUIi10hQqb3YwIdnrTcHCRnonTJgsCfVXuXNaBFEhkNp2gTKXdQkguVaBDYKHIdX1l6uq8HmHFHp8-q4zKoXhj2FBF4dZU4D-7kuG76Uz8WKu5Eol-XGwwOJ7nOnA',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)