import time
from datetime import datetime
import hashlib
import hmac
import config
import requests
import logging
import json
import urllib.parse

# headers

# log_file_date = datetime.now().strftime("%Y%m%d")
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S') # filename=f"logs/set_{set}_{log_file_date}.log")


def get_response(payload, api_method, resource):

    # payload = ''
    api_key = config.api_key
    api_secret = config.api_secret
    api_endpoint = config.api_endpoint
    api_ts = str(int(time.time() * 1000))
    api_contentHash = hashlib.sha512(payload.encode()).hexdigest()
    api_subaccountId = ""   # empty string
    # api_method = "GET"  # GET, POST
    api_url = f"{api_endpoint}/{resource}"
    logging.info(api_url)

    preSign = api_ts + api_url + api_method + api_contentHash
    api_signature = hmac.new(api_secret.encode(), preSign.encode(), hashlib.sha512).hexdigest()
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Api-Key': api_key,
        'Api-Timestamp': api_ts,
        'Api-Content-Hash': api_contentHash,
        'Api-Signature': api_signature,
    }

    response = requests.get(url=api_url, headers=headers).json()
    return response


def get_balance():
    resource = "balances"
    payload = ""
    api_method = "GET"
    balances = get_response(payload, api_method, resource)
    logging.info(balances)


def get_openorders(pair):
    resource = f"orders/open?{urllib.parse.urlencode({'marketSymbol': pair})}"
    payload = ""
    api_method = "GET"
    openorders = get_response(payload, api_method, resource)
    logging.info(openorders)


def get_orderhistory(pair):
    resource = f"orders/closed?{urllib.parse.urlencode({'marketSymbol': pair})}"
    payload = ""
    api_method = "GET"
    orderhist = get_response(payload, api_method, resource)
    logging.info(orderhist)


if __name__ == '__main__':
    # get_balance()
    # get_openorders('XRP-USD')
    # get_orderhistory('BTC-USD')
    pass
'''

def buylimit(market, quantity, rate):
    return query('POST', 'orders', {'marketSymbol': market, 'direction': 'BUY', 'type': 'LIMIT', 'timeInForce': 'GOOD_TIL_CANCELLED', 'quantity': quantity, 'limit': rate})

def selllimit(market, quantity, rate):
    return query('POST', 'orders', {'marketSymbol': market, 'direction': 'SELL', 'type': 'LIMIT', 'timeInForce': 'GOOD_TIL_CANCELLED', 'quantity': quantity, 'limit': rate})

def cancel(uuid):
    return query('DELETE', 'orders', uuid)

#print (getbalance())
#print (getopenorders('XRP-USD'))
#print (buylimit('XRP-USD', '60', '0.10000000'))
#print (selllimit('XRP-USD', '100', '0.20000000'))
#print (getorderhistory('XRP-USD'))
#print (cancel('orderid-bla-bla-bla'))
'''



