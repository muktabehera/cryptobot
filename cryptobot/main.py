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

log_file_date = datetime.now().strftime("%Y%m%d")
logger = logging.getLogger(__name__)
logging.basicConfig(level=config.logging_level, format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',  filename=f"logs/cryptobot_{log_file_date}.log")

def slack(msg):
    data = {"text": msg}
    headers = {"Content-Type": "application/json"}
    url = 'https://hooks.slack.com/services/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'
    slack_response =  requests.post(url=url, headers=headers, data=str(data))
    logging.info(f"status code = {str(slack_response.status_code)}")
    return str(slack_response.status_code)


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
    '''
    resource = "orders"
    payload = f"{{'marketSymbol': '{marketsymbol}', 'direction': 'SELL', 'type': 'MARKET', 'timeInForce': 'IMMEDIATE_OR_CANCEL', 'quantity': {qty}}}"
    api_method = "POST"
    sell_order_details = get_response(payload, api_method, resource)
    logging.info(sell_order_details)
    return sell_order_details


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

    marketsymbol = config.marketsymbol
    currencysymbol = config.currencysymbol

    commission_percentage = float(config.commission_percentage)        # .20% each side, total .40%. This should be 0.004, but left as is for now.
    slippage_buffer = float(config.slippage_buffer)                 # set to 0 since we're using mid range for bid and ask rates

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
    # logging.info(open_order)

    ticker = get_ticker(marketsymbol)
    # {'symbol': 'XRP-USD', 'lastTradeRate': '0.17600000', 'bidRate': '0.17587000', 'askRate': '0.17644000'}
    ask_rate = float(ticker['askRate'])
    bid_rate = float(ticker['bidRate'])
    sell_rate = (ask_rate + bid_rate) / 2

    usd_balance = get_balance('USD')
    usd_balance = float(usd_balance['available'])

    logging.info(f"USD balance = {usd_balance} current ask_rate: {ask_rate}, bid_rate = {bid_rate}, sell_rate = {sell_rate}")

    if open_order:
        open_order_exists = True
        qty = open_order['quantity']
        logging.info(f"open order exists for {qty} {marketsymbol}")
    else:
        logging.info("no open order found")
        # get current account balance
        balance = get_balance(currencysymbol)
        # logging.info(f"Balance = {order}")

        if float(balance['available']) > 0.000:
            # sell route
            qty = float(balance['available'])
            logging.info(f"{qty} units of {currencysymbol} available to sell")
            # get buy price
            # since there's balance get most recent buy order id
            recent_orders = get_closed_orders(marketsymbol)

            if recent_orders and recent_orders[0]['direction'] == 'BUY':    # double check

                # logging.info(recent_orders[0])
                recent_buy_order_id = recent_orders[0]['id']
                recent_buy_order_commission =float(recent_orders[0]['commission'])
                recent_buy_order_createdAt = recent_orders[0]['createdAt']
                recent_buy_order_closedAt = recent_orders[0]['closedAt']
                recent_buy_order_proceeds = float(recent_orders[0]['proceeds'])
                # get buy price and qty filled from that order
                qty = float(recent_orders[0]['fillQuantity'])
                buy_price = (recent_buy_order_proceeds + recent_buy_order_commission) / qty
                logging.info(f"recent {marketsymbol} buy price = {buy_price}")

                # check if current selling rate > buy_price + slippage + commission

                # get sell rate
                # ticker = get_ticker(marketsymbol)
                # {'symbol': 'XRP-USD', 'lastTradeRate': '0.17600000', 'bidRate': '0.17587000', 'askRate': '0.17644000'}
                # ask_rate = float(ticker['askRate'])
                # bid_rate = float(ticker['bidRate'])
                # sell_rate = (ask_rate + bid_rate) / 2

                # logging.info(f"current ask_rate: {ask_rate}, bid_rate = {bid_rate}, sell_rate = {sell_rate}")

                # calculate expected commision
                total_commission = qty * sell_rate * commission_percentage
                logging.info(f"total commission = ${total_commission}")

                sell_ready_price = buy_price + (buy_price * slippage_buffer) + total_commission
                logging.info(f"sell ready price = ${sell_ready_price}")

                if sell_rate > sell_ready_price:
                    sell_signal = True
                    logging.info(f"issue sell for {qty} units of {marketsymbol} @ {sell_rate}")
                    message = f"issued sell for {qty} units of {marketsymbol} @ {sell_rate}"
                    sell_order_details = sell(marketsymbol, qty)
                    slack(message)
                    time.sleep(5)
                    slack(json.dumps(sell_order_details))
                else:
                    logging.info(f"not ready to sell {qty} units of {marketsymbol} @ {sell_rate}")
        else:
            logging.info(f"{marketsymbol} balance = {float(balance['available'])}")
            logging.info(f"evaluating buy signal")

            # buy strategy:
                # price crosses ema series from below, buy
                # price crosses ema series from above, sell
                # https://www.learndatasci.com/tutorials/python-finance-part-3-moving-average-trading-strategy/

            close_1h = get_candles(marketsymbol, 'HOUR_1')['close'] # list of closes
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
                buy_qty = (float(usd_balance) - (float(usd_balance) * (commission_percentage/2))) / sell_rate
                message = f"issued buy for {buy_qty} units of {marketsymbol} @ 1 Hour close price of {close_1h[-1]}"
                logging.info(message)
                buy_order_details = buy(marketsymbol, buy_qty)
                slack(message)
                time.sleep(5)
                slack(json.dumps(buy_order_details))
            else:
                logging.info(f"no buy signal @ {close_1h[-1]}")
                pass

    # msg = {'x': 10}
    # x = json.dumps(msg)
    # slack(x)
    logging.info("end of run\n\n")
    pass


