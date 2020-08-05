import time
from datetime import datetime
import hashlib
import hmac
import config
import requests
import logging
import json
import urllib.parse
import numpy as np
import talib    # https://mrjbq7.github.io/ta-lib/

from requests.auth import AuthBase
import base64, os

'''config.py structure


LIVE_TRADE = False
api_key = ''
api_secret = ''
api_pass = ''

if LIVE_TRADE:
    api_endpoint = 'https://api.pro.coinbase.com/'
    api_key = ''
    api_secret = ''
    api_pass = ''
else:
    api_endpoint = 'https://api-public.sandbox.pro.coinbase.com/'    # sandbox
    api_key = ''
    api_secret = ''
    api_pass = ''

logging_level = 20  # https://docs.python.org/3/library/logging.html#logging-levels
#debug: 10, info: 20, warning: 30, error: 40,

product_id = 'BTC-USD'  # on sandbox only BTC-USD works
currencysymbol = 'BTC'

profit_target = 0.00     # 5% used as profit

'''


# Auth ref: https://github.com/dhull33/Coinbase-Crypto-Bot/blob/master/coinbasepro/private/coinbase_auth.py

log_file_date = datetime.now().strftime("%Y%m%d")
logger = logging.getLogger(__name__)
logging.basicConfig(level=config.logging_level, format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', ) # filename=f"logs/coinbase_{log_file_date}.log")


def slack(msg):
    data = {"text": msg}
    headers = {"Content-Type": "application/json"}
    url = 'https://hooks.slack.com/services/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'
    slack_response = requests.post(url=url, headers=headers, data=str(data))
    logging.info(f"status code = {str(slack_response.status_code)}")
    return str(slack_response.status_code)


# Create custom authentication for Exchange
class CoinbaseAuth(AuthBase):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())

        # logging.info(request.method)
        # logging.info(type(request.body))

        message = timestamp + request.method + request.path_url + (
                request.body or '')

        message = message.encode('utf-8')
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message, hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest())

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        })
        return request


def get_response(payload, api_method, resource):

    api_url = config.api_endpoint
    auth = CoinbaseAuth(config.api_key, config.api_secret, config.api_pass)

    if api_method == "POST":
        response = requests.post(api_url + resource, data=json.dumps(payload), auth=auth).json()
    elif api_method == "DELETE":
        response = requests.post(api_url + resource, data=json.dumps(payload), auth=auth).json()
    else:
        response = requests.get(api_url + resource, auth=auth).json()

    return response


def get_balance(currencySymbol):
    resource = f"accounts"
    payload = ""
    api_method = "GET"
    balances = get_response(payload, api_method, resource)
    # logging.info(balances)
    for i in balances:
        if (i['currency']) == currencySymbol:
            balances = float(i['balance'])

    return balances


def get_open_orders(product_id):
    resource = f"orders?status=open&status=pending&status=active&{urllib.parse.urlencode({'product_id': product_id})}"
    payload = ""
    api_method = "GET"
    openorders = get_response(payload, api_method, resource)
    # logging.info(type(openorders)) -- list
    # logging.info(openorders)
    return openorders


def get_closed_orders(product_id):
    resource = f"orders?status=done&{urllib.parse.urlencode({'product_id': product_id})}"
    payload = ""
    api_method = "GET"
    closedorders = get_response(payload, api_method, resource)
    # logging.info(type(openorders)) -- list
    # logging.info(openorders)
    return closedorders


def get_order(order_id):
    resource = f"orders/{order_id}"
    payload = ""
    api_method = "GET"
    order = get_response(payload, api_method, resource)
    return order

def buy(product_id, qty):

    resource = 'orders'
    payload = {'product_id': product_id, 'side': 'buy', 'type': 'market', 'size': round(qty,8)}

    # payload = f"{{'size': '{qty}', 'side': 'buy', 'type': 'market', 'product_id': '{product_id}'}}"
    # logging.info(payload)
    api_method = "POST"
    buy_order_details = get_response(payload, api_method, resource)
    # logging.info(buy_order_details)
    return buy_order_details


def sell(product_id, qty):
    '''
    Place a mkt sell order.
    ref: https://docs.pro.coinbase.com/#place-a-new-order
    '''
    sell_order_details = ''
    resource = "orders"
    # type	[optional] limit or market (default is limit)
    payload = {'size': qty, 'side': 'sell', 'type': 'market', 'product_id': product_id }
    api_method = "POST"
    sell_order_details = get_response(payload, api_method, resource)
    # logging.info(sell_order_details)
    return sell_order_details


def get_ticker(product_id):
    resource = f"products/{product_id}/ticker"
    payload = ""
    api_method = "GET"
    ticker = get_response(payload, api_method, resource)
    # logging.info(ticker)
    return ticker


def get_candles(product_id, granularity):

    # https://docs.pro.coinbase.com/#get-historic-rates
    # The granularity field must be one of the following values: {60, 300, 900, 3600, 21600, 86400}.
    # These values correspond to timeslices representing one minute, five minutes, fifteen minutes, one hour, six hours, and one day

    resource = f"products/{product_id}/candles?{urllib.parse.urlencode({'granularity': granularity})}"
    payload = ""
    api_method = "GET"
    r_candles = get_response(payload, api_method, resource)
    # [ time, low, high, open, close, volume ],

    close = list()
    vol = list()

    for i in r_candles:
        close.append(i[4])
        vol.append(i[5])

    return {'close': close, 'vol': vol}


if __name__ == '__main__':

    product_id = config.product_id
    currencysymbol = config.currencysymbol
    profit_target = float(config.profit_target)                 # set to 0 since we're using mid range for bid and ask rates

    sell_signal = False
    buy_signal = False

    qty = 0.000                 # float, 3 places of decimal
    buy_price = None
    balance_gt_0 = False    # USD balance greater than 0

    open_order_exists = False   # open order exists
    order_exists = False        # order exists
    offer_exists = False        # ask price and vol exist  and account for slippage and commission

    ## --> Trading Rules:
        # Only 1 open order at a time
        # Open an order only if previous order has been closed
        # Always Buy then sell, never sell first

    ## --> Trade Flow
        # check if open order exists, if yes, skip
        # if no, check balance of symbol
        # set order_exists = True

    logging.info("checking for open order")
    open_order = get_open_orders(product_id)
    # logging.info(f"open_order = {open_order}")

    ticker = get_ticker(product_id)
    #  {'trade_id': 98836669, 'price': '11285.85', 'size': '0.00458548', 'time': '2020-08-03T22:32:13.482861Z', 'bid': '11283.8', 'ask': '11285.79', 'volume': '13557.82455244'}

    ask = float(ticker['ask'])
    bid = float(ticker['bid'])
    sell_rate = (ask + bid) / 2     # average of bid and ask to set sell price for sell order, if met

    usd_balance = float(get_balance('USD'))

    logging.info(f"USD Balance = {usd_balance} current ask: {ask}, bid = {bid}, sell_rate = {sell_rate}")

    if open_order:
        open_order_exists = True
        qty = open_order['quantity']
        logging.info(f"open order exists for {qty} {product_id}")
    else:
        logging.info("no open order found")
        # get current account balance
        balance = float(get_balance(currencysymbol))
        # logging.info(f"Balance = {order}")

        if balance > 0.000:
            # sell route
            qty = balance
            logging.info(f"{qty} units of {currencysymbol} available to sell")
            # get buy price
            # since there's balance get most recent buy order id
            recent_orders = get_closed_orders(product_id)

            # logging.info(get_closed_orders(product_id))
            # [{'id': 'bf49332c-2d79-4696-9b12-52d445c9c739', 'product_id': 'BTC-USD', 'profile_id': '936e3ac5-6d7f-4f45-9208-248523553d1e', 'side': 'buy', 'funds': '9.9502487500000000', 'specified_funds': '10.0000000000000000', 'type': 'market', 'post_only': False, 'created_at': '2020-08-03T22:37:50.748626Z', 'done_at': '2020-08-03T22:37:50.754Z', 'done_reason': 'filled', 'fill_fees': '0.0497511995175000', 'filled_size': '0.00088335', 'executed_value': '9.9502399035000000', 'status': 'done', 'settled': True}]

            if recent_orders and recent_orders[0]['side'] == 'buy':    # double check

                # logging.info(recent_orders[0])

                recent_buy_order_id = recent_orders[0]['id']
                recent_buy_order_proceeds = float(recent_orders[0]['funds'])
                buy_price = float(recent_orders[0]['executed_value']) / float(recent_orders[0]['filled_size'])
                fill_fees = float(recent_orders[0]['fill_fees']) * 2    # to calculate both ways

                logging.info(f"recent {product_id} buy price = {buy_price}")

                sell_ready_price = buy_price + fill_fees + (buy_price * profit_target)
                expected_profit = round(((sell_ready_price - buy_price) * qty), 3)

                logging.info(f"sell ready price = ${sell_ready_price} expected profit: {expected_profit}")

                if sell_rate > sell_ready_price:
                    sell_signal = True
                    logging.info(f"issue sell for {qty} units of {product_id} @ {sell_rate}")

                    sell_order_details = sell(product_id, qty)  # price is not required for market orders
                    sell_order_id = sell_order_details['id']
                    time.sleep(10)   # wait for order to fill
                    order_deets = get_order(sell_order_id)
                    profit = float(order_deets['executed_value']) - recent_buy_order_proceeds
                    message = f"sold {float(order_deets['filled_size'])} units of {product_id} for ${profit} profit"
                    logging.info(message)
                    # slack(message)
                    # time.sleep(5)
                    # slack(json.dumps(order_deets))
                else:
                    logging.info(f"not ready to sell {qty} units of {product_id} @ {sell_rate}")
        else:
            logging.info(f"{product_id} balance = {float(balance)}")
            logging.info(f"evaluating buy signal")

            # buy strategy:
                # price crosses ema series from below, buy
                # price crosses ema series from above, sell
                # https://www.learndatasci.com/tutorials/python-finance-part-3-moving-average-trading-strategy/

            close_1h = get_candles(product_id, 21600)['close'] # Hour = 21600

            close_1h.reverse() # need to verify this

            np_close_1h = np.asarray(close_1h, dtype=float)

            # type numpy array
            np_close_ema20_1h = talib.EMA(np_close_1h, timeperiod=20)
            np_price_diff = np.subtract(np_close_1h, np_close_ema20_1h)
            # logging.info(f"Last 10 price to 20ema diff = {np_price_diff[-10:]}")  # last 10
            np_price_diff = np.where(np_price_diff > 0, 1, -1)  # set positive as 1, negative as -1

            # logging.info(f"Last 10 price = {close_5m[-10:]}")  # last 10
            # logging.info(f"Last 10 20ema = {np_close_ema20_5m[-10:]}")  # last 10
            logging.info(f"Last 10 price to 20ema diff = {np_price_diff[-10:]}")   # last 10

            # logging.info(f"np_price_diff[-1] {np_price_diff[-1]} > np_price_diff[-2] {np_price_diff[-2]}")

            if np_price_diff[-1] > np_price_diff[-2]:   # i.e price was below ema and now its above

                logging.info(f"buy signal @ {close_1h[-1]}")
                buy_signal = True
                buy_qty = float(usd_balance) / sell_rate

                message = f"issued buy for {buy_qty} units of {product_id} @ 1 Hour close price of {close_1h[-1]}"
                logging.info(message)

                buy_order_details = buy(product_id, buy_qty)
                buy_order_id = buy_order_details['id']

                logging.info(f"buy_order_id = {buy_order_id}")
                time.sleep(10)
                buy_order_deets = get_order(buy_order_id)
                actual_buy_qty = float(buy_order_deets['filled_size'])
                actual_buy_rate = float(buy_order_deets['executed_value']/actual_buy_qty)
                actual_buy_fees = float(buy_order_deets['fill_fees'])
                actual_buy_funds = float()
                message = f"bought {actual_buy_qty} units of {product_id} @ {actual_buy_rate}, fees = {actual_buy_fees}, funds = {actual_buy_funds}"
                logging.info(message)
                # slack(message)
                # slack(json.dumps(buy_order_deets))
            else:
                logging.info(f"no buy signal @ {close_1h[-1]}")
                pass

    logging.info("end of run\n\n")
    pass