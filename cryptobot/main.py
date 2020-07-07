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
    # logging.info(api_url)

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
        response = requests.post(url=api_url, data=payload, headers=headers).json()
    elif api_method == "DELETE":
        response = requests.delete(url=api_url, headers=headers).json()
    else:
        response = requests.get(url=api_url, params=payload, headers=headers).json()

    return response


def get_balance(currencySymbol):
    resource = f"balances/{currencySymbol}"
    payload = ""
    api_method = "GET"
    balances = get_response(payload, api_method, resource)
    return balances


def get_total_balances():
    resource = "balances"
    payload = ""
    api_method = "GET"
    total_balances = get_response(payload, api_method, resource)
    # logging.info(total_balances)
    return total_balances


def get_open_orders(marketSymbol):
    resource = f"orders/open?{urllib.parse.urlencode({'marketSymbol': marketSymbol})}"
    payload = ""
    api_method = "GET"
    openorders = get_response(payload, api_method, resource)
    # logging.info(type(openorders)) -- list
    # logging.info(openorders)
    return openorders


def get_closed_orders(marketSymbol):
    resource = f"orders/closed?{urllib.parse.urlencode({'marketSymbol': marketSymbol})}"
    payload = ""
    api_method = "GET"
    closedorders = get_response(payload, api_method, resource)
    # logging.info(closedorders)
    return closedorders


def get_order_details(orderid):
    resource = f"orders/{orderid}"
    payload = ""
    api_method = "GET"
    orderDetails = get_response(payload, api_method, resource)
    # logging.info(orderDetails)
    return orderDetails


def get_order_executions(orderid):
    resource = f"orders/{orderid}/executions"
    payload = ""
    api_method = "GET"
    orderexecutions = get_response(payload, api_method, resource)
    # logging.info(orderexecutions)
    return orderexecutions


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
    # logging.info(orderhist)
    return orderhist


def buy(marketsymbol, qty):

    resource = "orders"
    payload = f"{{'marketSymbol': '{marketsymbol}', 'direction': 'BUY', 'type': 'MARKET', 'timeInForce': 'IMMEDIATE_OR_CANCEL', 'quantity': {qty}}}"
    logging.info(f"Buy Payload = {payload}")
    api_method = "POST"
    buy_order_details = get_response(payload, api_method, resource)
    logging.info(buy_order_details)
    return buy_order_details
    # {'id': 'e5a52228-7c79-458a-b41c-6e40dd9f0988', 'marketSymbol': 'BTC-USD', 'direction': 'BUY', 'type': 'MARKET', 'quantity': '0.01027115', 'timeInForce': 'IMMEDIATE_OR_CANCEL', 'fillQuantity': '0.01025849', 'commission': '0.19050467', 'proceeds': '95.21448268', 'status': 'CLOSED', 'createdAt': '2020-07-07T02:29:33.76Z', 'updatedAt': '2020-07-07T02:29:33.76Z', 'closedAt': '2020-07-07T02:29:33.76Z'}


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
    sell = get_response(payload, api_method, resource)
    logging.info(sell)


def get_orderbook(marketSymbol):
    resource = f"markets/{marketSymbol}/orderbook"
    payload = ""
    api_method = "GET"
    orderbook = get_response(payload, api_method, resource)
    # logging.info(orderbook)
    return orderbook


def get_ticker(marketSymbol):
    resource = f"markets/{marketSymbol}/ticker"
    payload = ""
    api_method = "GET"
    ticker = get_response(payload, api_method, resource)
    # logging.info(ticker)
    return ticker


def get_candles(marketSymbol, candleInterval):

    # https://bittrex.github.io/api/v3#operation--markets--marketSymbol--candles--candleInterval--recent-get
    # MINUTE_1: 1 day, MINUTE_5: 1 day, HOUR_1: 31 days, DAY_1: 366 days

    resource = f"markets/{marketSymbol}/candles/{candleInterval}/recent"
    payload = ""
    api_method = "GET"
    r_candles = get_response(payload, api_method, resource)
    # logging.info(r_candles)

    close = list()
    vol = list()

    for i in r_candles:
        close.append(i['close'])
        vol.append(i['volume'])

    # logging.info(candles)
    # logging.info(len(candles))
    return {'close': close, 'vol': vol}


if __name__ == '__main__':

    marketsymbol = 'BTC-USD'
    currencysymbol = 'BTC'

    commission = 0.04           # .20% each side, total .40%
    slippage_buffer = 0.01

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
    open_order = get_open_orders(marketsymbol)
    logging.info(open_order)
    if open_order:
        open_order_exists = True
        qty = open_order['quantity']
        logging.info(f"open order exists for {qty} {marketsymbol}")
    else:
        logging.info("No open order found")
        # get current account balance
        balance = get_balance(currencysymbol)
        # logging.info(f"Balance = {order}")
        if float(balance['available']) > 0.000:
            balance_gt_0 = True
            qty = float(balance['available'])
            logging.info(f"{qty} units of {currencysymbol} available to sell")
            # get buy price
            # since there's balance get most recent buy order id
            recent_orders = get_closed_orders(marketsymbol)

            if recent_orders and recent_orders[0]['direction'] == 'BUY':

                logging.info(recent_orders[0])
                recent_buy_order_id = recent_orders[0]['id']
                recent_buy_order_commission = recent_orders[0]['commission']
                recent_buy_order_createdAt = recent_orders[0]['createdAt']
                recent_buy_order_closedAt = recent_orders[0]['closedAt']
                recent_buy_order_proceeds = recent_orders[0]['proceeds']
                # get buy price and qty filled from that order
                qty = recent_orders[0]['fillQuantity']
                buy_price = (recent_buy_order_proceeds + recent_buy_order_commission) / qty

                # check if current ask_price

        else:
            logging.info(f"0 units of {currencysymbol} available to sell")



    ticker = get_ticker(marketsymbol)
    # {'symbol': 'XRP-USD', 'lastTradeRate': '0.17600000', 'bidRate': '0.17587000', 'askRate': '0.17644000'}
    ask_rate = float(ticker['askRate'])
    logging.info(f"{currencysymbol} ask_rate (offer) = {ask_rate}")



    # if ask_rate >=

    # sell_signal
        # if order exists
        # if ask (offer) >= buy_price + (buy_price * commission) + slippage

    sell_signal = order_exists and offer_exists
    
    if sell_signal:
        logging.info(f"sell {qty} at market")
        # sell(marketsymbol, qty)

    # logging.info("cancelling order 'd91ba2c1-3ec8-428c-bc48-0073483e0734'")
    # cancel_order('d91ba2c1-3ec8-428c-bc48-0073483e0734')

    # get_balance('BTC')  # 'USD'
    # get_total_balances()
    # get_open_orders('XRP-USD')
    # logging.info(get_order_history('BTC-USD'))
    # get_order_details('5d3fc794-8f32-42e3-850c-ecd642b5b763') # orderid
    # get_order_executions('5d3fc794-8f32-42e3-850c-ecd642b5b763')
    # cancel_order('5d3fc794-8f32-42e3-850c-ecd642b5b763')    # {'code': 'ORDER_NOT_OPEN'}
    # buy('BTC-USD', 0.01027115)
    # sell_market('XRP-USD', '100')
    # get_orderbook('XRP-USD')
    # get_ticker('XRP-USD')
    # get_closed_orders('BTC-USD')
    # get_open_orders('BTC-USD')
    # logging.info(get_candles('XRP-USD', 'DAY_1')['close'])
    # logging.info(get_candles('XRP-USD', 'DAY_1')['vol'])

    # Strategy
    # 50, 200 SMA (buy)


    pass



