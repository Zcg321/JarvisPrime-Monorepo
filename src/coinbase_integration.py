import os
import json
import requests
import jwt
import datetime
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

# === LOAD ENV VARIABLES ===
load_dotenv()
API_KEY = os.getenv('API_KEY')
PRIVATE_KEY_FILE = os.getenv('PRIVATE_KEY_FILE')

# === LOAD PRIVATE KEY ===
with open(PRIVATE_KEY_FILE, 'rb') as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None
    )

# === GENERATE JWT ===
def generate_jwt():
    now = datetime.datetime.now(datetime.timezone.utc)  # Fixed UTC time
    payload = {
        'iss': API_KEY,
        'sub': API_KEY,
        'aud': 'coinbase-cloud',
        'iat': now,
        'exp': now + datetime.timedelta(minutes=5)
    }
    token = jwt.encode(payload, private_key, algorithm='ES256')
    return token

# === GET ACCOUNT BALANCES ===
def get_balances():
    url = 'https://api.coinbase.com/api/v3/brokerage/accounts'
    headers = {
        'Authorization': f'Bearer {generate_jwt()}',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    print("Status Code:", response.status_code)
    print("Response Text:", response.text)  # RAW output (no JSON)
    return response.text

# === RUN ===
if __name__ == '__main__':
    balances = get_balances()
    print(balances)  # Show raw output
