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
env = ''

if LIVE_TRADE:
    api_endpoint = 'https://api.pro.coinbase.com/'
    api_key = ''
    api_secret = ''
    api_pass = ''
    env = 'Live'

else:
    api_endpoint = 'https://api-public.sandbox.pro.coinbase.com/'    # sandbox
    api_key = ''
    api_secret = ''
    api_pass = ''
    env = 'Sandbox'

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
                    datefmt='%Y-%m-%d %H:%M:%S', filename=f"logs/coinbase_{log_file_date}.log")


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
    low = list()
    # vol = list()

    for i in r_candles:
        close.append(i[4])  # close
        low.append(i[1])    # low
        # vol.append(i[5])

    return {'close': close, 'low': low}     #, 'vol': vol}


if __name__ == '__main__':

    product_id = config.product_id
    percentage_resistance_threshold = float(config.per_resistance_threshold)
    env = config.env
    currencysymbol = config.currencysymbol
    profit_target = float(config.profit_target)                 # set to 0 since we're using mid range for bid and ask rates

    sell_signal = False
    buy_signal = False

    qty = 0.000                 # float, 3 places of decimal
    buy_price = None
    balance_gt_0 = False    # USD balance greater than 0

    order_exists = False        # order exists
    offer_exists = False        # ask price and vol exist  and account for slippage and commission

    support = -999999999        # really low random val
    resistance = 99999999999    # really high random val

    sell_ready_price = None

    logging.info(f"--------{env}---------")

    close_1h = get_candles(product_id, 3600)['close']  # 1H = 3600, 15Min = 900
    close_1h.reverse()  # verified
    np_close_1h = np.asarray(close_1h, dtype=float)

    # 50 ma
    np_close_ma50_1h = talib.MA(np_close_1h, timeperiod=50)
    # 200 ma
    np_close_ma200_1h = talib.MA(np_close_1h, timeperiod=200)

    close = float(np_close_1h[-1])              # current closing price

    ma_200 = float(np_close_ma200_1h[-1])       # 200 simple moving average
    ma_50 = float(np_close_ma50_1h[-1])       # 400 simple moving average

    logging.info(f"close = {close} ma_200 = {ma_200} ma_50 = {ma_50}")

    ## support and resistance

    # if price > 400 ma, support = 400 ma and resistance = 200 ma
    # if price > 200 ma, support = 200 ma and resistance = max(price in last 24 hrs)
    # if price > 400 ma and < 200 ma, support = 400 ma, resistance = 50 ma, 200 ma

    if close >= ma_200 and close <= ma_50:
        support = ma_200
        resistance = ma_50
    elif close >= ma_50 and close <= ma_200:
        support = min(np_close_1h[-24:])        # ma_50
        resistance = ma_200
    elif close <= ma_200:                       # and ma_50 < ma_200:
        resistance = ma_50                      # TODO: rethink to use ma_50 as resistance
        support = min(np_close_1h[-24:])        # i.e. in last 24hrs
    elif close >= ma_50 and close >= ma_200:
        support = ma_50
        resistance = max(np_close_1h[-24:])      # i.e. in last 24hrs

    resistance_threshold = resistance - (resistance * percentage_resistance_threshold)
    logging.info(f"support = {support} resistance = {resistance} resistance_threshold [{percentage_resistance_threshold*100}%] = {resistance_threshold}")

    ## --> Trading Rules:
        # Only 1 open order at a time
        # Open an order only if previous order has been closed
        # Buy and then sell, sell and then buy

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

                # set sell ready price
                profit_price = float(buy_price + fill_fees + (buy_price * profit_target))
                sell_ready_prices = [profit_price, resistance]

                if profit_price <= resistance:
                    sell_ready_price = profit_price
                    logging.info(f"using profit target ({profit_target * 100}%) = ${profit_price} for sell ready price")
                else:
                    sell_ready_price = resistance
                    logging.info(f"using resistance = ${resistance} for sell ready price [profit target ({profit_target * 100}%)]")

                expected_profit = round(((sell_ready_price - buy_price) * qty), 3)

                logging.info(f"sell ready price = ${sell_ready_price} expected profit: {expected_profit}")

                if sell_rate > sell_ready_price:
                    sell_signal = True
                    logging.info(f"issue sell for {qty} units of {product_id} @ {sell_rate}")

                    sell_order_details = sell(product_id, qty)  # price is not required for market orders
                    sell_order_id = sell_order_details['id']
                    time.sleep(20)   # wait for order to fill
                    sell_order_deets = get_order(sell_order_id)
                    profit = float(sell_order_deets['executed_value']) - recent_buy_order_proceeds
                    message = f"[Coinbase][{env}] SOLD {float(sell_order_deets['filled_size'])} units of {product_id} for ${round(profit, 2)} profit"
                    logging.info(message)
                    slack(message)
                    time.sleep(5)
                    slack(json.dumps(sell_order_deets))
                else:
                    logging.info(f"not ready to sell {qty} units of {product_id} @ {sell_rate}")
        else:
            logging.info(f"{product_id} balance = {float(balance)}")
            logging.info(f"evaluating buy signal")

            # buy strategy:

            # with ma_50 > ma_200,
            # ma_200 trending up (last 5 diffs positive)
            # price cuts 200 from below

            # with ma_50 < ma_200
            # ma_200 trending up (last 5 diffs positive)
            # price cuts 200 from below
            # buy mkt sell at resistance


            buy_signal = False

            price_gte_support = False       # gt than or equal to
            price_lte_resistance_threshold = False    # less than or equal to
            ma_200_trending_up = False

            if close >= support:
                price_gte_support = True
                logging.info(f"Close [{close} >= support [{support}] = {price_gte_support}")

            if close <= resistance_threshold:
                price_lte_resistance_threshold = True
                logging.info(f"Close [{close} <= resistance_threshold [{resistance_threshold}]")

            price_cuts_50ma_from_bottom = False
            price_cuts_200ma_from_bottom = False

            np_200ma_trend_diff = np.diff(np_close_ma200_1h)
            np_200ma_trend_diff = np_200ma_trend_diff[-10:]  # last 5 hourly
            if np_200ma_trend_diff.all() > 0:
                ma_200_trending_up = True
                logging.info(f"ma_200_trending_up = {ma_200_trending_up}")
            else:
                logging.info(f"ma_200_trending_up = {ma_200_trending_up}")

            np_price_diff_50ma = np.subtract(np_close_1h, np_close_ma50_1h)
            np_price_diff_200ma = np.subtract(np_close_1h, np_close_ma200_1h)

            # logging.info(f"Last 10 price to 50ma diff = {np_price_diff_50ma[-10:]}")    # last 10
            # logging.info(f"Last 10 price to 200ma diff = {np_price_diff_200ma[-10:]}")  # last 10

            np_price_diff_50ma = np.where(np_price_diff_50ma > 0, 1, -1)    # set positive as 1, negative as -1
            np_price_diff_200ma = np.where(np_price_diff_200ma > 0, 1, -1)  # set positive as 1, negative as -1

            logging.info(f"Last 10 price to 50ma diff = {np_price_diff_50ma[-10:]}")  # last 10
            logging.info(f"Last 10 price to 200ma diff = {np_price_diff_200ma[-10:]}")  # last 10

            if np_price_diff_200ma[-1] > np_price_diff_200ma[-2]:
                price_cuts_200ma_from_bottom = True

            if np_price_diff_50ma[-1] > np_price_diff_50ma[-2]:
                price_cuts_50ma_from_bottom = True

            logging.info(f"np_price_diff_200ma[-1] {np_price_diff_200ma[-1]} > np_price_diff_200ma[-2] {np_price_diff_200ma[-2]} = {price_cuts_200ma_from_bottom}")

            logging.info(f"np_price_diff_50ma[-1] {np_price_diff_50ma[-1]} > np_price_diff_50ma[-2] {np_price_diff_50ma[-2]} = {price_cuts_50ma_from_bottom}")
            # buy strategy:

            # with ma_50 > ma_200,
            # ma_200 trending up (last 5 diffs positive)
            # price cuts 200 from below
            # with ma_50 > ma_200,
            # ma_200 trending up (last 5 diffs positive)
            # price cuts 50 from below

            # with ma_50 < ma_200
            # ma_200 trending up (last 5 diffs positive)
            # price cuts 200 from below
            # buy mkt sell at resistance

            # with ma_50 < ma_200
            # ma_200 trending up (last 5 diffs positive)
            # price cuts 50 from below

            if ((ma_50 > ma_200) and ma_200_trending_up and price_lte_resistance_threshold) and (price_cuts_50ma_from_bottom or price_cuts_200ma_from_bottom):
                buy_signal = True
                logging.info(f"Buy condition 1 satisfied")
            elif ((ma_50 < ma_200) and ma_200_trending_up and price_lte_resistance_threshold) and (price_cuts_50ma_from_bottom or price_cuts_200ma_from_bottom):
                buy_signal = True
                logging.info(f"Buy condition 2 satisfied")
            else:
                logging.info(f"CONDITION 1: ((ma_50 {ma_50} > ma_200 {ma_200}) and ma_200_trending_up {ma_200_trending_up} and price_lte_resistance_threshold {price_lte_resistance_threshold}) and (price_cuts_50ma_from_bottom {price_cuts_50ma_from_bottom} or price_cuts_200ma_from_bottom {price_cuts_200ma_from_bottom})")
                logging.info(f"CONDITION 2: ((ma_50 < ma_200) and ma_200_trending_up {ma_200_trending_up} and price_lte_resistance_threshold {price_lte_resistance_threshold}) and (price_cuts_50ma_from_bottom {price_cuts_50ma_from_bottom} or price_cuts_200ma_from_bottom{price_cuts_200ma_from_bottom})")

            if buy_signal:
                logging.info(f"buy signal @ {close_1h[-1]}")
                buy_signal = True
                buy_qty = float(usd_balance) / sell_rate

                message = f"issued buy for {buy_qty} units of {product_id} @ 1 Hr close price of {close_1h[-1]}"
                logging.info(message)

                buy_order_details = buy(product_id, buy_qty)
                buy_order_id = buy_order_details['id']

                logging.info(f"buy_order_id = {buy_order_id}")

                time.sleep(20)  # give it time to fill

                buy_order_deets = get_order(buy_order_id)
                actual_buy_qty = float(buy_order_deets['filled_size'])
                actual_buy_rate = float(buy_order_deets['executed_value'])/actual_buy_qty
                actual_buy_fees = float(buy_order_deets['fill_fees'])
                actual_buy_funds = float(buy_order_deets['funds'])
                message = f"[Coinbase][{env}] BOUGHT {actual_buy_qty} units of {product_id} @ {actual_buy_rate}, fees = {actual_buy_fees}, funds = {actual_buy_funds}"
                logging.info(message)
                slack(message)
                time.sleep(5)
                slack(json.dumps(buy_order_deets))
            else:
                logging.info(f"no buy signal @ {close_1h[-1]}")
                pass

    logging.info("end of run\n\n")
    pass



