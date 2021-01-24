from flask import Flask
from flask import request

import requests
import json

from flask_caching import Cache

config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "simple", # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}

app = Flask(__name__)
# tell Flask to use the above defined config
app.config.from_mapping(config)
cache = Cache(app)

API_KEY = "7b9d9766-6314-420e-9039-5eac1610c8f0"
ETH_ID = 1027
BTC_ID = 1

def get_price(id):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    parameters = {
    'id': id,
    'convert':'USD'
    }
    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': API_KEY,
    }

    session = requests.Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        print(data)
    except (requests.ConnectionError, requests.Timeout, requests.TooManyRedirects) as e:
        print(e)
    price = data['data'][str(id)]['quote']['USD']['price']
    return str(price)

@app.route('/eth')
@cache.cached(timeout=120)
def eth():
    return get_price(ETH_ID)

@app.route('/btc')
@cache.cached(timeout=120)
def btc():
    return get_price(BTC_ID)