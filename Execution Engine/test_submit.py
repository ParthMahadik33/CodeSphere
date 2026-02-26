import requests
import json

url = 'http://127.0.0.1:5000/submit'
data = {
    'code': "print('hello world')"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
