import time
from datetime import datetime
import hashlib
import hmac
import config
import requests
import logging
import json
import urllib.parse
# import numpy as np

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

    if api_method == "POST":
        response = requests.post(url=api_url, data=json.dumps(payload), headers=headers).json()
    elif api_method == "DELETE":
        response = requests.delete(url=api_url, headers=headers).json()
    else:
        response = requests.get(url=api_url, params=payload, headers=headers).json()

    return response


def get_balance(pair):
    resource = f"balances/{pair}"
    payload = ""
    api_method = "GET"
    balances = get_response(payload, api_method, resource)
    logging.info(balances)


def get_total_balances():
    resource = "balances"
    payload = ""
    api_method = "GET"
    balances = get_response(payload, api_method, resource)
    logging.info(balances)


def get_open_orders(pair):
    resource = f"orders/open?{urllib.parse.urlencode({'marketSymbol': pair})}"
    payload = ""
    api_method = "GET"
    openorders = get_response(payload, api_method, resource)
    logging.info(openorders)


def get_order_details(orderid):
    resource = f"orders/{orderid}"
    payload = ""
    api_method = "GET"
    orderDetails = get_response(payload, api_method, resource)
    logging.info(orderDetails)


def get_order_executions(orderid):
    resource = f"orders/{orderid}/executions"
    payload = ""
    api_method = "GET"
    orderexecutions = get_response(payload, api_method, resource)
    logging.info(orderexecutions)



def cancel_order(orderid):
    resource = f"orders/{orderid}"
    payload = ""
    api_method = "DELETE"
    cancelorder = get_response(payload, api_method, resource)
    logging.info(cancelorder)


def get_order_history(pair):
    resource = f"orders/closed?{urllib.parse.urlencode({'marketSymbol': pair})}"
    payload = ""
    api_method = "GET"
    orderhist = get_response(payload, api_method, resource)
    logging.info(orderhist)


def buy(marketSymbol, qty):
    resource = "orders"
    payload = f"{'marketSymbol': {marketSymbol}, 'direction': 'BUY', 'type': 'MARKET', 'timeInForce': 'GOOD_TIL_CANCELLED', 'quantity': {qty}}"
    api_method = "POST"
    buylimit = get_response(payload, api_method, resource)
    logging.info(buylimit)


def sell(marketSymbol, qty):
    '''
    Place a limit sell order.
    ref: https://bittrex.github.io/api/v3#definition-NewOrder
    :param symbol:
    :param qty:
    :param rate:
    :return:
    '''
    resource = "orders"
    payload = f"{'marketSymbol': {marketSymbol}, 'direction': 'BUY', 'type': 'MARKET', 'timeInForce': 'GOOD_TIL_CANCELLED'}"
    api_method = "POST"
    selllimit = get_response(payload, api_method, resource)
    logging.info(selllimit)


def get_orderbook(marketSymbol):
    resource = f"markets/{marketSymbol}/orderbook"
    payload = ""
    api_method = "GET"
    orderbook = get_response(payload, api_method, resource)
    logging.info(orderbook)


def get_candles(marketSymbol, candleInterval):

    # https://bittrex.github.io/api/v3#operation--markets--marketSymbol--candles--candleInterval--recent-get
    # MINUTE_1: 1 day, MINUTE_5: 1 day, HOUR_1: 31 days, DAY_1: 366 days

    resource = f"markets/{marketSymbol}/candles/{candleInterval}/recent"
    payload = ""
    api_method = "GET"
    r_candles = get_response(payload, api_method, resource)
    # logging.info(r_candles)

    candles = list()
    for i in r_candles:
        candles.append(i['close'])

    # logging.info(candles)
    # logging.info(len(candles))
    return candles




if __name__ == '__main__':

    # get_balance('USD')
    # get_total_balances()
    # get_open_orders('XRP-USD')
    # get_order_history('BTC-USD')
    # get_order_details('5d3fc794-8f32-42e3-850c-ecd642b5b763') # orderid
    # get_order_executions('5d3fc794-8f32-42e3-850c-ecd642b5b763')
    # cancel_order('5d3fc794-8f32-42e3-850c-ecd642b5b763')    # {'code': 'ORDER_NOT_OPEN'}
    # buy_market('XRP-USD', '100')
    # sell_market('XRP-USD', '100')
    # get_orderbook('XRP-USD')
    get_candles('XRP-USD', 'DAY_1')

    pass



