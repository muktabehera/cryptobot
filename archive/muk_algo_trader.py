# TODO: Add Exception handling (Connection Error, etc)

# import alpaca_trade_api as tradeapi
import pandas as pd
import time
import logging
from archive import muk_config as config
import requests
import json
import argparse

from datetime import datetime
import pytz  # for timezones
import dateutil.parser
# ref: https://medium.com/@eleroy/10-things-you-need-to-know-about-date-and-time-in-python-with-datetime-pytz-dateutil-timedelta-309bfbafb3f7

import numpy as np
import random
# from sklearn import linear_model

nyc = pytz.timezone('America/New_York')


headers = {
    "APCA-API-KEY-ID": config.APCA_API_KEY_ID,
    "APCA-API-SECRET-KEY": config.APCA_API_SECRET_KEY,
    "Content-Type": "application/json"
}

slack_headers = {
    "Content-Type": "application/json"
}


def slackit(channel, msg):

    '''
    :param msg: text to be posted
           channel: channel to post
    :return: response.text (ok)
    '''

    slack_headers = {
        "Content-Type": "application/json"
    }

    data = {"text": msg}

    slack_url = ''

    if config.slack_channel == 'LIVE':
        slack_url = "https://hooks.slack.com/services/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"  # ADD BEFORE RUNNLING LIVE!
    else: # config.slack_channel == 'PAPER':
        slack_url = "https://hooks.slack.com/services/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"

    if channel == 'CHECK':
        slack_url = "https://hooks.slack.com/services/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"

    if channel == 'ERROR':
        slack_url = "https://hooks.slack.com/services/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"

    response = requests.post(url=slack_url, headers=slack_headers, data=str(data))
    return response.text


def get_ts():
    '''
    Get all timestamps to be used in the algo
    :return: dict of all timestamps (ts)
    '''

    ts_dict = dict()

    clock = requests.get(url=clock_uri, headers=headers).json()

    # next_open_ts = dateutil.parser.parse(clock['next_open'])
    # next_close_ts = dateutil.parser.parse(clock['next_close'])
    clock_ts = dateutil.parser.parse(clock['timestamp'])

    is_open = clock['is_open']

    # SET START AND END TIMES
    end_time = clock_ts

    # Get when the market opens or opened today

    nyc = pytz.timezone('America/New_York')
    today_ts = datetime.today().astimezone(nyc)
    today_str = datetime.today().astimezone(nyc).strftime('%Y-%m-%d')
    now = datetime.now().astimezone(nyc).strftime('%Y-%m-%d %H:%M:%S')

    # https://pandas.pydata.org/pandas-docs/stable/user_guide/timedeltas.html

    cal_uri = f"{config.base_url}/calendar?start={today_ts.strftime('%Y-%m-%d')}&end={today_ts.strftime('%Y-%m-%d')}"
    cal = requests.get(cal_uri, headers=headers).json()

    open_ts_pst = dateutil.parser.parse(today_ts.strftime('%Y-%m-%d') + ' ' + cal[0]['open']) - pd.Timedelta("180 Minutes")
    # to make it tz aware for num_bars calculation
    open_ts_nyc = open_ts_pst.astimezone(nyc)
    open_ts = open_ts_nyc

    close_ts_pst = dateutil.parser.parse(today_ts.strftime('%Y-%m-%d') + ' ' + cal[0]['close']) - pd.Timedelta("180 Minutes")
    close_ts_nyc = close_ts_pst.astimezone(nyc)
    close_ts = close_ts_nyc

    open_ts_str = datetime.strptime(today_ts.strftime('%Y-%m-%d') + ' ' + cal[0]['open'], '%Y-%m-%d %H:%M')
    close_ts_str = datetime.strptime(today_ts.strftime('%Y-%m-%d') + ' ' + cal[0]['close'], '%Y-%m-%d %H:%M')

    closing_window = config.closing_window  # in Mins - > time in min left for market to close
    about_to_close_ts = close_ts - pd.Timedelta(f'{closing_window} Minutes')
    # current_timestamp + 60 mins

    market_about_to_close = False  # default market is not closing in the next 30 min

    if clock_ts >= about_to_close_ts:
        market_about_to_close = True  # if there are 30 min left for market to close

    # start_1m = end_time - pd.Timedelta('1 Minutes')
    # start_5m = end_time - pd.Timedelta('5 Minutes')
    # start_15m = end_time - pd.Timedelta('15 Minutes')
    # start_dt = end_time - pd.Timedelta('1 Days')

    # log_end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')  # 2019-03-04 02:05:58
    # log_end_dt = start_1m.strftime('%Y-%m-%d')  # 2019-03-04
    # log_start_1m = start_1m.strftime('%Y-%m-%d %H:%M:%S')  # 2019-03-04 02:05:58
    # log_start_5m = start_5m.strftime('%Y-%m-%d %H:%M:%S')  # 2019-03-04 02:05:58
    # log_start_15m = start_15m.strftime('%Y-%m-%d %H:%M:%S')  # 2019-03-04 02:05:58
    # log_start_dt = start_dt.strftime('%Y-%m-%d')  # '2019-03-04'

    ts_dict = {
        "is_open": is_open,
        # "next_open_ts" : next_open_ts,
        # "next_close_ts": next_close_ts,
        "clock_ts": clock_ts,   # current timestamp from the clock
        "end_time": end_time,
        "today_ts": today_ts,
        "today_str": today_str,
        "now": now,
        "open_ts": open_ts,
        "close_ts": close_ts,
        "closing_window": closing_window,
        "market_about_to_close": market_about_to_close,
        # "start_1m": start_1m,
        # "start_5m": start_5m,
        # "start_15m": start_15m,
        # "log_end_time": log_end_time,
        # "log_end_dt": log_end_dt,
        # "log_start_1m": log_start_1m,
        # "log_start_5m": log_start_5m,
        # "log_start_15m": log_start_15m,
        # "log_start_dt": log_start_dt
    }

    logging.debug(ts_dict)

    return ts_dict


def fetch_bars(data_provider):       # data_provider = config.data_provider

    # np_hl_1m = np.array([])
    # np_ll_1m = np.array([])
    np_cl_1m = np.array([])
    # np_vl_1m = np.array([])
    np_tl_1m = np.array([])
    # float_np_tl_1m = np.array([])

    # TODO: pull bars async
    # TODO: Convert bar_interval as a method instead of 1Min, 5Min sections

    # start_ts = ts['open_ts']  # market open ts
    # logging.info(f'start_ts:                   {start_ts}')
    # end_ts = ts['clock_ts']  # current ts
    # logging.info(f'end_ts:                     {end_ts}')
    # market_close_ts = ts['close_ts']  # to prevent getting more bars after market has closed for the day
    # logging.info(f'market_close_ts:                    {market_close_ts}')

    limit_1m = config.limit_1m
    # limit_5m = config.limit_5m
    # limit_15m = config.limit_15m

    if data_provider == 'alpaca':

        ################################# GET 1 MIN BARS #################################

        bar_interval = "1Min"

        payload_1m = {
            "symbols": arg_ticker,
            "limit": limit_1m
            # "start": ts['log_start_1m'],
            # "end": ts['log_end_time']
        }
        base_uri_1m = f'{config.data_url}/bars/{bar_interval}'
        bars_1m = requests.get(url=base_uri_1m, params=payload_1m, headers=headers).json()

        for i, v1m in enumerate(bars_1m[arg_ticker]):
            # CONVERT UNIX TS TO READABLE TS
            v1m_ts_nyc = datetime.fromtimestamp(v1m['t']).astimezone(nyc)  # Covert Unix TS to NYC NOT UTC!!
            v1m_ts = v1m_ts_nyc.strftime('%Y-%m-%d %H:%M:%S')  # Convert to str with format

            # APPEND TO LIST

            # append 1m bars to list
            # ol_1m.append(v1m['o'])
            # ll_1m.append(v1m['l'])
            # hl_1m.append(v1m['h'])
            cl_1m.append(v1m['c'])
            # vl_1m.append(v1m['v'])
            tl_1m.append(v1m_ts)
            # float_tl_1m.append(v1m['t'])  # to get float ts for linear regression

            # convert to 1m np array
            # added datatype float to avoid real is not double error during MOM cacl
            # np_ol_1m = np.array(ol_1m, dtype=float)
            # np_hl_1m = np.array(hl_1m, dtype=float)
            # np_ll_1m = np.array(ll_1m, dtype=float)
            np_cl_1m = np.array(cl_1m, dtype=float)
            # np_vl_1m = np.array(vl_1m, dtype=float)
            np_tl_1m = np.array(tl_1m)
            # float_np_tl_1m = np.array(float_tl_1m, dtype=float)

            # round to 2 decimal places

            # np_ol_1m = np.round(np_ol_1m, 2)
            # np_hl_1m = np.round(np_hl_1m, 2)
            # np_ll_1m = np.round(np_ll_1m, 2)
            np_cl_1m = np.round(np_cl_1m, 2)
            # np_vl_1m = np.round(np_vl_1m, 2)

            # no need to round of time np arrays

        # logging.info(f'np_tl_1m    {len(np_tl_1m)}  np_cl_1m    {len(np_cl_1m)}')

        bars_response = {

            # "np_ol_1m": np_ol_1m,
            # "np_hl_1m": np_hl_1m,
            # "np_ll_1m": np_ll_1m,
            "np_cl_1m": np_cl_1m,
            # "np_vl_1m": np_vl_1m,
            "np_tl_1m": np_tl_1m,
            # "float_np_tl_1m": float_np_tl_1m
        }

        logging.debug(f"bars_response : {bars_response}")

        return bars_response

    elif data_provider == 'polygon':

        ################################# GET 1 MIN BARS #################################

        bar_interval = "minute"

        payload_1m = {
            "apiKey": config.APCA_API_KEY_ID,
            # "start": ts['open_ts']
            "limit": limit_1m
        }

        # data_url = f'https://api.polygon.io/{data_api_version}/historic/agg'
        base_uri_1m = f'{config.data_url}/{bar_interval}/{arg_ticker}'

        bars_1m = requests.get(url=base_uri_1m, params=payload_1m).json()

        for i, v1m in enumerate(bars_1m['ticks']):
            # CONVERT UNIX TS TO READABLE TS

            # Extra step: Divide Polygon's ts by 1000 to convert to seconds from milliseconds
            v1m_ts_nyc = datetime.fromtimestamp(v1m['t']/1000).astimezone(nyc)  # Covert Unix TS to NYC NOT UTC!!
            v1m_ts = v1m_ts_nyc.strftime('%Y-%m-%d %H:%M:%S')  # Convert to str with format

            # v1m_ts = str(v1m['t']) # workaround since polygon ts don't return correct str timestamps

            # APPEND TO LIST

            # append 1m bars to list
            # ol_1m.append(v1m['o'])
            # ll_1m.append(v1m['l'])
            # hl_1m.append(v1m['h'])
            cl_1m.append(v1m['c'])
            # vl_1m.append(v1m['v'])
            tl_1m.append(v1m_ts)
            # float_tl_1m.append(v1m['t'])  # to get float ts for linear regression

            # convert to 1m np array
            # added datatype float to avoid real is not double error during MOM cacl
            # np_ol_1m = np.array(ol_1m, dtype=float)
            # np_hl_1m = np.array(hl_1m, dtype=float)
            # np_ll_1m = np.array(ll_1m, dtype=float)
            np_cl_1m = np.array(cl_1m, dtype=float)
            # np_vl_1m = np.array(vl_1m, dtype=float)
            np_tl_1m = np.array(tl_1m)
            # float_np_tl_1m = np.array(float_tl_1m, dtype=float)

            # round to 2 decimal places

            # np_ol_1m = np.round(np_ol_1m, 2)
            # np_hl_1m = np.round(np_hl_1m, 2)
            # np_ll_1m = np.round(np_ll_1m, 2)
            np_cl_1m = np.round(np_cl_1m, 2)
            # np_vl_1m = np.round(np_vl_1m, 2)

            # no need to round of time np arrays

        # logging.info(f'np_tl_1m    {len(np_tl_1m)}  np_cl_1m    {len(np_cl_1m)}')

        bars_response = {

            # "np_ol_1m": np_ol_1m,
            # "np_hl_1m": np_hl_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            # "np_ll_1m": np_ll_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            "np_cl_1m": np_cl_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            # "np_vl_1m": np_vl_1m[::-1],               # reverse the list since polygon data is orders in asc order
            "np_tl_1m": np_tl_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            # "float_np_tl_1m": float_np_tl_1m[::-1]    # reverse the list since polygon data is orders in asc order
        }

        logging.debug(f"bars_response : {bars_response}")

        return bars_response


if __name__ == '__main__':

    day_trade_minimum = config.day_trade_minimum

    buy_order_placed = dict()  # INITIALIZATION
    buy_order_details = dict()

    sell_order_placed = dict()
    sell_order_details = dict()

    # secs_to_sleep = config.secs_to_sleep          # check inside while

    order_uri = config.order_uri
    clock_uri = config.clock_uri

    actual_buy_price = 0.000  # float
    sell_price = 0.000  # float

    BUY_PRICE = np.array([0.000])  # initialize here, set to actual avg price at which asset was bought
    sell_target = np.array([0])  # initialization

    parser = argparse.ArgumentParser(description="apca - auto trader")

    parser.add_argument('-t', action="store", dest='arg_ticker',
                        help="symbol config, values include V, UBER, CTSH")   # symbol

    #
    # parser.add_argument('-s', action="store", dest='set',
    #                     help="symbol set from config, values include 1...5")   # symbol

    arg_val = parser.parse_args()

    arg_ticker = str(arg_val.arg_ticker)

    ticker_data = config.tickers[f"{arg_ticker}"]

    position_qty = 0    # default
    equity = 0.00       # default to 0
    equity_limit = 0.0  # default
    cash = 0.0          # default cash

    max_open_positions_allowed = int(config.max_open_positions_allowed)

    # logging.info(f"[START][{ticker}]")

    health_check_alert_counter = 0
    x = 0

    while True:  # infinite

        secs_to_sleep = random.randint(0, config.max_secs_to_sleep)

        # SET LOGGING LEVEL

        log_file_date = datetime.now().strftime("%Y%m%d")
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', filename=f"logs/{arg_ticker}_{log_file_date}.log")

        ts = get_ts()

        market_is_open = ts['is_open']  # check if market is open for trading

        # check if market just opened from ts response

        current_ts = ts['clock_ts']  # dup of end_ts, to be used for limiting past trades
        open_ts = ts['open_ts']
        close_ts = ts['close_ts']

        if market_is_open:
            trading_time_left = round((close_ts - current_ts).seconds/60)
        else:
            trading_time_left = 0

        # logging.info(f'[{ticker}] [{x}] market_is_open: {market_is_open} time_left:  {trading_time_left} mins')

        # new_bar_available = True

        if config.testing_algo_after_hours:                     ######### CHECK THIS ###########
            market_is_open = True

        start_time = datetime.now()  # to calculate ETA for all tickers

        if market_is_open:

            start_time = datetime.now()                         # to calculate ETA

            account = dict()                        # default for account response
            actual_buy_price = None            # default to 0 for each ticker

            position = False                        # default position to False
            positions_response = dict()             # reset to null dict for each ticker
            position_qty = 0  # default             # reset to default
            position_side = None                    # default position side (buy or sell)
            unrealized_intraday_pl = None           # default intraday pnl in a given open position

            equity = 0.00  # default to 0           # reset to default
            equity_limit = 0.0  # default           # reset to default
            cash = 0.0  # default cash              # reset to default

            # ol_1m = list()                        # reset to null for each ticker
            # hl_1m = list()
            # ll_1m = list()
            cl_1m = list()
            # vl_1m = list()
            tl_1m = list()
            # float_tl_1m = list()

            logging.info('--' * 40)
            logging.info(f'[{arg_ticker}] [{x}] market_is_open: {market_is_open} time_left:  {trading_time_left} mins')

            if config.live_trade:
                logging.info(f'[{arg_ticker}] !!! LIVE TRADE !!!')
            else:
                logging.info(f'[{arg_ticker}] ### PAPER TRADE ###')

            data_provider = config.data_provider
            logging.info(f"[{arg_ticker}] data provider:    {data_provider}")

            # ready to trade
            # TODO: Post Market Open and Close to SLACK

            ############ 0. Setup ############

            ############# GET ACCOUNT INFO

            account_uri = config.account_uri

            account = requests.get(url=account_uri, headers=headers).json()

            equity = float(account["equity"])       # equity
            cash = float(account["cash"])           # cash

            # shorting enabled with override
            # account_shorting_enabled = account["shorting_enabled"]  # Only short if enabled, else go long only!!
            # bool_shorting_enabled = account_shorting_enabled and config.allow_shorting  # Only short if enabled, else go long only!!

            # logging.info(f'[{arg_ticker}] bool_shorting_enabled = {bool_shorting_enabled}   config.allow_shorting: {config.allow_shorting}')

            current_open_positions = 0

            try:
                pos = requests.get(url=config.positions_uri, headers=headers).json()
                current_open_positions = len(pos)
            except Exception as e:
                logging.error(f'[{arg_ticker}] Error fetching current open positions : {str(e)}')


            ############# GET POSITION INFO

            ############  >_< CHECK IF A POSITION EXISTS FROM THE PREVIOUS TRADE ############

            ticker_positions_uri = f'{config.positions_uri}/{arg_ticker}'

            positions_response = None
            try:
                positions_response = requests.get(url=ticker_positions_uri, headers=headers).json()
            except Exception as e:
                logging.error(f'[{arg_ticker}] Error fetching position details : {str(e)}')

            # check if key exists in dict, code indicates error or no position

            if "code" not in positions_response:
                position = True
                position_qty = abs(int(positions_response['qty']))              # to make -ve units positive
                position_side = positions_response['side']  # long or short-0.0142711518858308-0.0142711518858308-0.0142711518858308
                unrealized_intraday_pl = float(positions_response["unrealized_intraday_pl"])  # dropping the decimals

                actual_buy_price = round(float(positions_response['avg_entry_price']), 2)

            # LIMIT TOTAL TRADABLE AMOUNT

            equity_less_daytrademin = equity - day_trade_minimum  # Total cash in account

            # LIMIT OPENING ONLY 1 POSITION AT A TIME

            # cash_limit = cash * config.position_size    # E.G 1 (100%) if trading one stock only

            equity_limit = equity_less_daytrademin / max_open_positions_allowed

            # TODO: ENABLE NEXT 2 lines
            # if current_open_positions >= max_open_positions_allowed:
            #     cash = 0

            if cash <= 0 and not position:          # else it exits even for stocks with open positions
                equity_limit = 0                    # added cash check to avoid margin trading
                logging.info(f'[{arg_ticker}] equity:   ${equity}   cash:   ${cash}     NO CASH AVAILABLE, EXITING')
                logging.info('--' * 40)
                # time.sleep(secs_to_sleep)
                continue

            logging.info(f'[{arg_ticker}] equity:   ${equity}   cash:   ${cash}')
            logging.info(f'[{arg_ticker}] current_open_positions: {current_open_positions}     max_open_positions_allowed: {max_open_positions_allowed}')
            logging.info(f'[{arg_ticker}] equity_limit: [${int(equity_limit)}] of [${int(equity_less_daytrademin)}] day_trade_minimum: [${day_trade_minimum}]')
            logging.info(f'[{arg_ticker}] current_position: [{position_qty}]    side:   [{position_side}]')
            logging.info(f'[{arg_ticker}] actual_buy_price:    $ {actual_buy_price}')

            # logging.info(f'[{ticker}] unrealized_intraday_pl:   ${unrealized_intraday_pl}')

            ############# GET OPEN ORDERS

            open_order_exists = False
            open_order_id = None
            open_order_symbol = None
            open_order_qty = None
            open_order_filled_qty = None

            # list all open orders

            null = None     # assign null to None to avoid the NameError: name 'null' is not defined in response
            open_orders = requests.get(url=order_uri, headers=headers).json()

            # https://stackoverflow.com/questions/8653516/python-list-of-dictionaries-search
            order = next((order for order in open_orders if order["symbol"] == arg_ticker), None)

            if order:
                open_order_exists = True
                open_order_id = order["id"]
                open_order_symbol = order["symbol"]
                open_order_qty = order["qty"]
                open_order_filled_qty = order["filled_qty"]

            logging.info(f'[{arg_ticker}] open_order_exists: [{open_order_exists}]    open_order_qty:   [{open_order_qty}]')

            ############ >_< FETCH TICKERS BASED ON CURRENT TS ############

            # logging.info(f'[{ticker}] BAR INTERVAL:    {bar_interval} Min')

            bars = fetch_bars(config.data_provider)  # for 1Min

            ############### 1 MIN ###############
            # np_ol_1m = bars['np_ol_1m']
            # np_hl_1m = bars['np_hl_1m']
            # np_ll_1m = bars['np_ll_1m']
            np_cl_1m = bars['np_cl_1m']
            # np_vl_1m = bars['np_vl_1m']
            np_tl_1m = bars['np_tl_1m']
            # float_np_tl_1m = bars['float_np_tl_1m']


            # logging.debug(f'[{ticker}] NP_OL_1M:    {np_ol_1m}')
            # logging.debug(f'[{arg_ticker}] np_hl_1m:    {np_hl_1m}')
            # logging.debug(f'[{arg_ticker}] np_ll_1m:    {np_ll_1m}')
            logging.debug(f'[{arg_ticker}] np_cl_1m:    {np_cl_1m}')
            # logging.debug(f'[{ticker}] np_vl_1m:    {np_vl_1m}')
            # logging.debug(f'[{ticker}] np_tl_1m:    {np_tl_1m}')      # TOO MUCH INFO FOR DEBUG

            ############# INDICATORS / CALCULATIONS ###########################

            bool_sell_target = False        # default
            bool_buy_price = False          # default
            buy_price = None                # default
            units_to_buy = None             # default
            bool_sell_price_above_buy = False   # default

            buy_price = float(ticker_data["buy_price"])    # value from config
            units_to_buy = int(equity_limit / buy_price )  # assign same value to both

            if np_cl_1m[-1] <= buy_price:
                bool_buy_price = True

            if position_qty > 0 or open_order_exists:
                units_to_buy = 0
                position = True                     # added since orders were being placed with 0 units and failing

            price_diff_to_sell = float(ticker_data["price_diff_to_sell"])

            if actual_buy_price:

                if (actual_buy_price + price_diff_to_sell) > price_diff_to_sell:    # so we don't get sell target as price increment value
                    sell_target = actual_buy_price + price_diff_to_sell
                else:
                    sell_target = None

            logging.info(f"[{arg_ticker}] [{np_cl_1m[-1]}] buy_price:   {buy_price} {bool_buy_price}  units_to_buy: {units_to_buy}  sell_target:    ${sell_target}   price_diff_to_sell: ${price_diff_to_sell}")

            ########################### BUY / SELL INDICATORS ####################

            bool_closing_time = ts['market_about_to_close']

            logging.info(f"[{arg_ticker}] bool_closing_time:    {bool_closing_time}")

            if actual_buy_price:
                bool_sell_price_above_buy = float(np_cl_1m[-1]) > (actual_buy_price + config.small_price_increment)
            # flag to indicate current price is gt buy price

            if sell_target:     # to avoid failing with None for sell_target during comparison
                bool_sell_target = float(np_cl_1m[-1]) >= float(sell_target)

            # current price > sell target

            logging.info(f"[{arg_ticker}] [{np_cl_1m[-1]}] bool_sell_price_above_buy:           {bool_sell_price_above_buy} [{np_cl_1m[-1]} > ({actual_buy_price} + {config.small_price_increment})]")
            logging.info(f"[{arg_ticker}] [{np_cl_1m[-1]}] bool_sell_target:                    {bool_sell_target} [{sell_target}]")




            ###########################################
            #####        LONG POSITION        ########
            ###########################################


            ################################ BUY SIGNAL  ###########################

            LONG_BUY_SIGNAL = bool_buy_price and not bool_closing_time

            logging.info(f'[{arg_ticker}] [{np_cl_1m[-1]}] long_buy_signal:                     {LONG_BUY_SIGNAL}  bool_buy_price: {bool_buy_price} [${buy_price}]')

            ################################ SELL SIGNAL ###########################

            bool_long_sell_signal = bool_sell_target or (bool_sell_price_above_buy and bool_closing_time)

            LONG_SELL_SIGNAL = bool_long_sell_signal

            # SELL only if a buy position exists.
            logging.info(f'[{arg_ticker}] [{np_cl_1m[-1]}] long_sell_signal:                    {LONG_SELL_SIGNAL}  bool_long_sell_signal: {bool_long_sell_signal} [${np_cl_1m[-1]}]')

            ################################################################
            ####    >>>>>>      TRADING ACTIONS          <<<<<<<<    #######
            ################################################################
            '''
            
            if not position and LONG_BUY_SIGNAL:
                # long buy
                pass
            if position and position_side == 'buy' and LONG_SELL_SIGNAL:
                # long sell
                pass                
            '''

            ################################ LONG BUY - Open New Long Positionm ######################################

            if LONG_BUY_SIGNAL and not position and not open_order_exists:  # if no position or open order exists and a buy sig is found

                # limit_price = buy_price

                # https://docs.alpaca.markets/api-documentation/web-api/orders/

                buy_order_data = {
                    'symbol': arg_ticker,
                    'qty': units_to_buy,
                    'side': 'buy',
                    'type': 'market',
                    # 'limit_price': limit_price,
                    'time_in_force': 'day'
                    # 'client_order_id': uuid.uuid4().hex    # generate order_id e.g. '9fe2c4e93f654fdbb24c02b15259716c'
                }
                buy_order_data = json.dumps(buy_order_data)

                logging.info(f'[{arg_ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [long_buy_signal] buy_order_data: {buy_order_data}')

                buy_order_sent = False
                buy_order_placed = None
                order_id = None

                try:
                    buy_order_placed = requests.post(url=order_uri, headers=headers,
                                                     data=buy_order_data).json()
                    buy_order_sent = True
                    order_id = buy_order_placed['id']

                    order_text = f"[{arg_ticker}] [{np_cl_1m[-1]} [ORDER] [long_buy_signal] [buy_order_id] {order_id}"
                    logging.info(order_text)
                    # slackit(channel=config.slack_channel, msg=order_text)

                except Exception as e:
                    error_text = f"[ERROR] [{arg_ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [long_buy_signal] Error placing order: {str(buy_order_placed['message'])}"
                    logging.info(error_text)
                    slackit(channel="ERROR", msg=error_text)

                buy_order_executed = False

                if buy_order_placed['status'] is not None:  # to check if order was placed

                    while not buy_order_executed:  # wait 10 tries

                        # keep checking until order is filled
                        # buy_order_details_data = {'order_id': order_id}
                        # buy_order_details_data = json.dumps(buy_order_details_data)

                        get_order_details_uri = f'{config.base_url}/orders/{order_id}'

                        buy_order_details = requests.get(url=get_order_details_uri, headers=headers).json()

                        logging.info(f"[{arg_ticker}] [LONG_BUY_SIGNAL] [BUY] [WAITING_TO_EXECUTE] [{buy_order_details['submitted_at']}] "
                              f"[{buy_order_details['status']}] {buy_order_details['side']} "
                              f"order for {buy_order_details['qty']} shares of {buy_order_details['symbol']}")

                        if buy_order_details['status'] == 'filled':  # or order_details.status == 'partially_filled':
                            buy_order_executed = True

                        logging.info(f"[{arg_ticker}] [long_buy_signal] buy_order_status:    {buy_order_placed['status']} ")

                        time.sleep(5)  # WAIT 5 SECS BEFORE NEXT CHECK
                    
                    ###############
                    buy_filled_avg_price = float(buy_order_details['filled_avg_price'])  # ACTUAL FROM BUY ORDER
                    ###############

                    sell_target = buy_filled_avg_price + price_diff_to_sell  # updated with actual buy_filled_avg_price

                    filled_at = buy_order_details['filled_at']
                    filled_qty = buy_order_details['filled_qty']

                    buy_order_text = f"[{arg_ticker}] [LONG_BUY_SIGNAL] {filled_at} {str(buy_order_details['side']).upper()} ORDER OF {filled_qty} [{arg_ticker}] EXECUTED @ {filled_avg_price} TARGET ${sell_target}"

                    logging.info(buy_order_text)

                    position = True # set position to True once BUY is executed
                    
                else:
                    logging.error(f"[{current_ts}] [ERROR] {buy_order_details['side']} ORDER WAS NOT PLACED")


            ################################ LONG_SELL - Close Existing Open Long Position ###########################

            if LONG_SELL_SIGNAL and position and position_side == 'long' and not open_order_exists:

                # https://docs.alpaca.markets/api-documentation/web-api/orders/

                sell_order_data = {
                    'symbol': arg_ticker,
                    'qty': position_qty,    # sell entire position
                    'side': 'sell',
                    'type': 'market',
                    # 'limit_price': limit_price,
                    'time_in_force': 'day'
                    # 'client_order_id': uuid.uuid4().hex    # generate order_id e.g. '9fe2c4e93f654fdbb24c02b15259716c'
                }
                sell_order_data = json.dumps(sell_order_data)

                logging.info(f'[{arg_ticker}] [$PL:{unrealized_intraday_pl}] [{np_cl_1m[-1]}] [long_sell_signal] sell_order_data:    {sell_order_data}')

                sell_order_sent = False
                sell_order_placed = None
                order_id = None

                try:
                    sell_order_placed = requests.post(url=order_uri, headers=headers,
                                                      data=sell_order_data).json()
                    sell_order_sent = True
                    order_id = sell_order_placed['id']

                    order_text = f"[{arg_ticker}] [$PL : {unrealized_intraday_pl}] [{np_cl_1m[-1]}] [ORDER] [long_sell_signal] [sell_order_id] [{order_id}]"
                    logging.info(order_text)
                    # slackit(channel=config.slack_channel, msg=order_text)

                except Exception as e:
                    error_text = f"[ERROR] [{arg_ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [long_sell_signal] Error placing order: {str(sell_order_placed['message'])}"
                    logging.info(error_text)
                    slackit(channel="ERROR", msg=error_text)

                sell_order_executed = False

                # logging.info(f"SELL Order Placed Status Code:           {sell_order_placed['status_code']} ")

                if sell_order_placed['status'] is not None:

                    while not sell_order_executed:

                        # keep checking until order is filled

                        get_order_details_uri = f'{config.base_url}/orders/{order_id}'

                        sell_order_details = requests.get(url=get_order_details_uri, headers=headers).json()

                        waiting_to_sell = f"[{arg_ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [LONG_SELL_SIGNAL] [SELL] [WAITING_TO_EXECUTE] [{sell_order_details['submitted_at']}] " \
                            f"[{sell_order_details['status']}] {sell_order_details['side']} " \
                            f"order for {sell_order_details['qty']} shares of {sell_order_details['symbol']}"

                        logging.info(waiting_to_sell)

                        # slackit(channel='apca-paper', msg=waiting_to_sell)

                        if sell_order_details['status'] == 'filled':  # or order_details.status == 'partially_filled':
                            sell_order_executed = True

                        logging.info(f"[{arg_ticker}] [LONG_SELL_SIGNAL] SELL ORDER STATUS:   {sell_order_placed['status']} ")

                        time.sleep(5)  # WAIT 10 SECS BEFORE NEXT CHECK

                    ###############
                    sell_filled_avg_price = round(float(sell_order_details['filled_avg_price']), 2)
                    ###############

                    filled_at = sell_order_details['filled_at']

                    side = str(sell_order_details['side']).upper()

                    profit = round((float(sell_price - buy_price) * position_qty), 2)

                    sell_order_text = f'[{arg_ticker}] [LONG_SELL_SIGNAL] [{filled_at}] [EXECUTED] {side} ORDER WAS EXECUTED @ {sell_filled_avg_price}'

                    logging.info(sell_order_text)

                    # slackit(channel='apca_paper', msg=sell_order_text)  # post to slack

                    trade_text = f'[{arg_ticker}] [LONG] BUY {position_qty} @ ${buy_price} SELL @ ${sell_price}  PNL ${profit}'

                    logging.info(trade_text)
                    slackit(channel=config.slack_channel, msg=trade_text)    # post to slack

                position = False  # set position to false once a sale has completed

            ###########################################################################################################

        # HEALTH CHECK START ------ >>

        # end_time = datetime.now() - start_time
        # logging.info(f"Finished {num_tickers} tickers in {end_time.seconds} seconds")

        if health_check_alert_counter == 1:
            msg = f'{arg_ticker} [CHECK] OK'
            slackit(channel="CHECK", msg=msg)                    # Post to health-check slack channel
        elif health_check_alert_counter > 360:
            health_check_alert_counter = 0

        health_check_alert_counter += 1

        # HEALTH CHECK END --------- <<

        x += 1

        # logging.info('\n')
        logging.info('--'*40)
        time.sleep(int(secs_to_sleep))
        logging.info(f'[{arg_ticker}] secs_to_sleep:   [{secs_to_sleep}]')


