# TODO: Add Exception handling (Connection Error, etc)

# import alpaca_trade_api as tradeapi
import pandas as pd
import time
import logging
import config
import requests
import json

from datetime import datetime
import pytz  # for timezones
import dateutil.parser
# ref: https://medium.com/@eleroy/10-things-you-need-to-know-about-date-and-time-in-python-with-datetime-pytz-dateutil-timedelta-309bfbafb3f7

import numpy as np
import talib  # https://mrjbq7.github.io/ta-lib/
import matplotlib

matplotlib.use('TkAgg')

# backend to use, valid strings are ['GTK3Agg', 'GTK3Cairo', 'MacOSX', 'nbAgg', 'Qt4Agg',
# 'Qt4Cairo', 'Qt5Agg', 'Qt5Cairo', 'TkAgg', 'TkCairo', 'WebAgg', 'WX', 'WXAgg', 'WXCairo',
# 'agg', 'cairo', 'pdf', 'pgf', 'ps', 'svg', 'template']

import matplotlib.pyplot as plt

# talib.get_functions()
# talib.get_function_groups()
import uuid


def num_bars(start_ts, end_ts, market_close_ts, num):

  if end_ts >= market_close_ts:
      end_ts = market_close_ts      # to not get more bars after market has closed

  if num == 1:
    diff_ts = round((end_ts - start_ts).total_seconds() / 60)
  elif num == 5:
    diff_ts = round(((end_ts - start_ts).total_seconds() / 60)/5)
  elif num == 15:
    diff_ts = round(((end_ts - start_ts).total_seconds() / 60)/15)
  else:
      print(f'interval not supported')

  return diff_ts


# SET LOGGING LEVEL
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

nyc = pytz.timezone('America/New_York')

# api = tradeapi.REST(
#     key_id=config.APCA_API_KEY_ID,
#     secret_key=config.APCA_API_SECRET_KEY,
#     base_url=config.APCA_PAPER_BASE_URL
# )

headers = {
    "APCA-API-KEY-ID": config.APCA_API_KEY_ID,
    "APCA-API-SECRET-KEY": config.APCA_API_SECRET_KEY,
    "Content-Type": "application/json"
}

clock_uri = config.clock_uri


def get_current_positions():

    positions_uri = config.positions_uri

    positions_response = requests.get(url=positions_uri, headers=headers).json()

    asset_id = positions_response['asset_id']
    num_stocks_unsold = float(positions_response['qty'])
    entry_price = float(positions_response['avg_entry_price'])     # target price should be based on the avg entry price

    if positions_response['side'] == 'long':
        bool_is_buy = True
    else:
        bool_is_buy = False

    positions = {
        "asset_id": asset_id,
        "num_stocks_unsold": num_stocks_unsold,
        "entry_price": entry_price,
        "bool_is_buy": bool_is_buy
    }

    return positions

def get_ts():
    '''
    Get all timestamps to be used in the algo
    :return: dict of all timestamps (ts)
    '''
    ts_dict = dict()

    clock = requests.get(url=clock_uri, headers=headers).json()

    next_open_ts = dateutil.parser.parse(clock['next_open'])
    next_close_ts = dateutil.parser.parse(clock['next_close'])
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

    cal_uri = f"https://paper-api.alpaca.markets/v1/calendar?start={today_ts.strftime('%Y-%m-%d')}&end={today_ts.strftime('%Y-%m-%d')}"
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
    about_to_close_ts = clock_ts - pd.Timedelta(f'{closing_window} Minutes')
    market_about_to_close = False  # default market is not closing in the next 30 min

    if clock_ts >= about_to_close_ts:
        market_about_to_close = True  # if there are 30 min left for market to close

    start_1m = end_time - pd.Timedelta('1 Minutes')
    start_5m = end_time - pd.Timedelta('5 Minutes')
    start_15m = end_time - pd.Timedelta('15 Minutes')
    start_dt = end_time - pd.Timedelta('1 Days')

    log_end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')  # 2019-03-04 02:05:58
    log_end_dt = start_1m.strftime('%Y-%m-%d')  # 2019-03-04
    log_start_1m = start_1m.strftime('%Y-%m-%d %H:%M:%S')  # 2019-03-04 02:05:58
    log_start_5m = start_5m.strftime('%Y-%m-%d %H:%M:%S')  # 2019-03-04 02:05:58
    log_start_15m = start_15m.strftime('%Y-%m-%d %H:%M:%S')  # 2019-03-04 02:05:58
    log_start_dt = start_dt.strftime('%Y-%m-%d')  # '2019-03-04'

    ts_dict = {
        "is_open": is_open,
        "next_open_ts" : next_open_ts,
        "next_close_ts": next_close_ts,
        "clock_ts": clock_ts,   # current timestamp from the clock
        "end_time": end_time,
        "today_ts": today_ts,
        "today_str": today_str,
        "now": now,
        "open_ts": open_ts,
        "close_ts": close_ts,
        "closing_window": closing_window,
        "market_about_to_close": market_about_to_close,
        "start_1m": start_1m,
        "start_5m": start_5m,
        "start_15m": start_15m,
        "log_end_time": log_end_time,
        "log_end_dt": log_end_dt,
        "log_start_1m": log_start_1m,
        "log_start_5m": log_start_5m,
        "log_start_15m": log_start_15m,
        "log_start_dt": log_start_dt
    }

    return ts_dict


def fetch_bars(bar_interval):

    # TODO: pull bars async

    start_ts = ts['open_ts']            # market open ts
    # print(f'start_ts:                   {start_ts}')
    end_ts = ts['clock_ts']             # current ts
    # print(f'end_ts:                     {end_ts}')
    market_close_ts = ts['close_ts']    # to prevent getting more bars after market has closed for the day
    print(f'market_close_ts:                    {market_close_ts}')

    # paper_limit_5m = num_bars(start_ts=start_ts, end_ts=end_ts, market_close_ts=market_close_ts, num=5)

    paper_limit_5m = config.paper_limit_5m
    paper_limit_1m = config.paper_limit_1m

    # print(f'paper_limit_5m:                   {paper_limit_5m}')

    # if int(bar_interval) == 5:
    bar_interval = "5Min"
    base_uri_5m = f'https://data.alpaca.markets/v1/bars/{bar_interval}'
    payload_5m = {
        "symbols": ticker,
        "limit": paper_limit_5m,
        "start": ts['log_start_5m'],
        "end": ts['log_end_time']
    }
    bars_5m = requests.get(url=base_uri_5m, params=payload_5m, headers=headers).json()

    # elif int(bar_interval) == 1:
    bar_interval = "1Min"
    payload_1m = {
        "symbols": ticker,
        "limit": paper_limit_1m,
        "start": ts['log_start_1m'],
        "end": ts['log_end_time']
    }
    base_uri_1m = f'https://data.alpaca.markets/v1/bars/{bar_interval}'
    bars_1m = requests.get(url=base_uri_1m, params=payload_1m, headers=headers).json()


    for i, v5m in enumerate(bars_5m[ticker]):
        # CONVERT UNIX TS TO READABLE TS
        v5m_ts_nyc = datetime.fromtimestamp(v5m['t']).astimezone(nyc)  # Covert Unix TS to NYC NOT UTC!!
        v5m_ts = v5m_ts_nyc.strftime('%Y-%m-%d %H:%M:%S')  # Convert to str with format

        # APPEND TO LIST

        # append 5m bars to list
        ol_5m.append(v5m['o'])
        ll_5m.append(v5m['l'])
        hl_5m.append(v5m['h'])
        cl_5m.append(v5m['c'])
        vl_5m.append(v5m['v'])

        tl_5m.append(v5m_ts)

        # convert to 5m np array
        np_ol_5m = np.array(ol_5m)
        np_hl_5m = np.array(hl_5m)
        np_ll_5m = np.array(ll_5m)
        np_cl_5m = np.array(cl_5m)
        np_vl_5m = np.array(vl_5m)
        np_tl_5m = np.array(tl_5m)

    # print(f'np_tl_5m    {len(np_tl_5m)}  np_cl_5m    {len(np_cl_5m)}')

    for i, v1m in enumerate(bars_1m[ticker]):
        # CONVERT UNIX TS TO READABLE TS
        v1m_ts_nyc = datetime.fromtimestamp(v1m['t']).astimezone(nyc)  # Covert Unix TS to NYC NOT UTC!!
        v1m_ts = v1m_ts_nyc.strftime('%Y-%m-%d %H:%M:%S')  # Convert to str with format

        # APPEND TO LIST

        # append 5m bars to list
        ol_1m.append(v1m['o'])
        ll_1m.append(v1m['l'])
        hl_1m.append(v1m['h'])
        cl_1m.append(v1m['c'])
        vl_1m.append(v1m['v'])

        tl_1m.append(v1m_ts)

        # convert to 5m np array
        np_ol_1m = np.array(ol_1m)
        np_hl_1m = np.array(hl_1m)
        np_ll_1m = np.array(ll_1m)
        np_cl_1m = np.array(cl_1m)
        np_vl_1m = np.array(vl_1m)
        np_tl_1m = np.array(tl_1m)

    # print(f'np_tl_1m    {len(np_tl_1m)}  np_cl_1m    {len(np_cl_1m)}')

    bars_response = {
        "np_cl_5m": np_cl_5m,
        "np_tl_5m": np_tl_5m,
        "np_cl_1m": np_cl_1m,
        "np_tl_1m": np_tl_1m
    }

    return bars_response

# TODO: Add ETAs at each step


if __name__ == '__main__':

    # next_trade_ts = (datetime.now() + pd.Timedelta("1 Minutes")).astimezone(nyc)  # default initialization to a future date
    # TODO: determine use ts from api vs now

    ticker = config.ticker
    bar_interval = config.bar_interval
    order_uri = config.order_uri

    # x = 0

    while True:  # infinite

        print('*'*80)
        print('\n')

        # Reset the lists each run to null
        tl_5m = list()
        ol_5m = list()
        hl_5m = list()
        ll_5m = list()
        cl_5m = list()
        vl_5m = list()

        tl_1m = list()
        ol_1m = list()
        hl_1m = list()
        ll_1m = list()
        cl_1m = list()
        vl_1m = list()

        # print(f'Entering x =        {x}')

        ts = get_ts()

        market_is_open = ts['is_open']  # check if market is open for trading

        ######### FOR AFTER HOUR TESTS ONLY #########

        # market_is_open = True

        #############################################

        print(f'market_is_open                      {market_is_open}')

        current_ts = ts['clock_ts']  # dup of end_ts, to be used for limiting past trades
        print(f'current_ts:                         {current_ts}')

        # check if market just opened
        open_ts = ts['open_ts']
        print(f'open_ts:                            {open_ts}')

        new_bar_available = True

        if market_is_open:

            # ready to trade

            # 0. Setup
            # Add positionSizing = 0.25 for each stock
            # cash_balance = get_cash_balance()

            # >_< CHECK IF A POSITION EXISTS FROM THE PREVIOUS TRADE

            positions_uri = config.positions_uri

            positions_response = requests.get(url=positions_uri, headers=headers).json()

            position = False  # default position to False

            if 'code' in positions_response:        # check if key exists in dict

                if int(positions_response['code']) == 40410000:
                    position = False
                    num_stocks_unsold = 0
                else:
                    asset_id = positions_response['asset_id']
                    num_stocks_unsold = float(positions_response['qty'])

                    positions = {
                        "asset_id": asset_id,
                        "num_stocks_unsold": num_stocks_unsold,
                    }

            print(f'position:                           {position}')

            # >_< FETCH TICKERS BASED ON CURRENT TS

            bar_interval = config.bar_interval

            ############### 5 MIN ###############

            if bar_interval == 5:    # for 5 Min

                print(f'RUNNING 5 MIN BARS')

                bars = fetch_bars(bar_interval=bar_interval)  # 1 for 1Min, 5 for 5Min, 15 for 15Min

                np_cl_5m = bars['np_cl_5m']
                np_tl_5m = bars['np_tl_5m']

                # print(f'np_cl_5m:               {np_cl_5m}')
                # print(f'np_tl_5m:               {np_tl_5m}')

                # GET MOMENTUM
                mom_5m = talib.MOM(np_cl_5m, timeperiod=1)

                # print(f'mom_5m:               {mom_5m}')

                # TODO: Cancel order if not executed in 5 min (optional)

                signals = []

                BUY_PRICE = np.array([0.000])  # initialize here, set to actual avg price at which asset was bought

                sell_target_based_on_profit_percentage = np.array([0])  # initialization

                buy_price = 0.000   # float
                sell_price = 0.000  # float
                list_trade_profit = list()  # list to hold profit amount
                list_trade_pnl = list()  # dict to hold profit or loss for each trade
                day_pnl = 0.000  # for the day (float)

                trade_left_open = False  # to check if a trade was left open, initial False

                units_to_trade = config.units_to_trade
                # TODO: [IMPORTANT] derive units to trade dynamically based on cash balance and position size
                # TODO: handle partial fills (optional)

                ###########################

                # Profit percentage (price above buy price) 25% as 0.25, 10% as 0.1
                # used to set -> sell_target_based_on_profit_percentage

                profit_percentage = float(config.profit_percentage)  # 0.2 for 20%

                print(f'profit percentage                   {profit_percentage}')

                ###################     5 MIN BARS START    #######################

                # for i in range(len(np_cl_5m)):

                # STRATEGY 2: BUY if mom 2 > mom 1, SELL mom1, mom2 < 0 and current price > buy

                bool_closing_time = ts['market_about_to_close']
                bool_buy_momentum = (mom_5m[-1] > 0 and mom_5m[-2] > 0) and (mom_5m[1] > mom_5m[-2])

                ################################

                BUY_SIGNAL = bool_buy_momentum  # and not bool_closing_time

                print(f'[{np_cl_5m[-1]}] BUY_SIGNAL                 {BUY_SIGNAL}')

                # TODO: [IMPORTANT] include closing time check in actual trades

                ################################

                bool_sell_momentum = mom_5m[-1] < 0 and mom_5m[-2] < 0  # current and prev momentum are positive

                bool_sell_price = float(np_cl_5m[-1]) > float(BUY_PRICE[-1])  # current price is gt buy price
                # print(f'bool_sell_price [{bool_sell_price}] = float(np_cl_5m[i]) [{float(np_cl_5m[i])}] > float(BUY_PRICE[0]) [{float(BUY_PRICE[0])}]')

                bool_sell_profit_target = float(np_cl_5m[-1]) >= float(
                    sell_target_based_on_profit_percentage)  # current price > sell target
                # print(f'[{np_tl_5m[i]}] bool_sell_profit_target {bool_sell_profit_target} = float(np_cl_5m[i]) {float(np_cl_5m[i])} >= float(sell_target_based_on_profit_percentage) {float(sell_target_based_on_profit_percentage)}')

                # TODO: [IMPORTANT] don't use int, it drops the decimal places during comparison, use float instead

                ################################

                SELL_SIGNAL = (bool_sell_momentum and bool_sell_price) or \
                              bool_sell_profit_target  # or \
                # (bool_sell_price and position and bool_closing_time)  # TODO: Incorporate closing time

                print(f'[{np_cl_5m[-1]}] SELL_SIGNAL                {SELL_SIGNAL}')

                # print(f'[{np_tl_5m[i]}] [{round(np_cl_5m[i], 2)}]     '
                #       f'[SELL]      {SELL_SIGNAL}            '
                #       f'MOMENTUM    {bool_sell_momentum}          '
                #       f'POSITION    {position}              '
                #       f'CLOSING     {bool_closing_time}          '
                #       f'SELLPRICE     {bool_sell_price}          '
                #       f'PROFIT_TARGET [{sell_target_based_on_profit_percentage}] {bool_sell_profit_target}  ')

                ################################

                if np.isnan(mom_5m[-1]):
                    continue
                else:

                    ################### BUY ##################

                    if not position and BUY_SIGNAL:  # if no position exists and a buy sig is found

                        # TODO: check clock and don't buy 30 min before market close

                        BUY_PRICE[0] = float((np_cl_5m[-1] + np_cl_5m[-2]) / 2)   # for limit price only
                        buy_price = round(BUY_PRICE[0], 3)                          # for limit price only

                        # limit_price = BUY_PRICE[0]

                        # https://docs.alpaca.markets/api-documentation/web-api/orders/

                        buy_order_data = {
                            'symbol': ticker,
                            'qty': config.units_to_trade,
                            'side': 'buy',
                            'type': 'market',
                            # 'limit_price': limit_price,
                            'time_in_force': 'day'
                            # 'client_order_id': uuid.uuid4().hex    # generate order_id e.g. '9fe2c4e93f654fdbb24c02b15259716c'
                        }
                        buy_order_data = json.dumps(buy_order_data)

                        print(f'BUY ORDER DATA:    {buy_order_data}')

                        buy_order_sent = False

                        try:
                            buy_order_placed = requests.post(url=order_uri, headers=headers, data=buy_order_data).json()
                            buy_order_sent = True
                            order_id = buy_order_placed['id']   # order_id
                        except Exception as e:
                            print(f'Error placing order: {str(e)}')

                        buy_order_executed = False

                        print(f"Order Placed Status Code:           {buy_order_placed['status_code']} ")

                        if buy_order_placed['status_code'] == 200:

                            while not buy_order_executed:

                                # keep checking until order is filled
                                buy_order_details_data = {'order_id': order_id}
                                buy_order_details = requests.get(url=order_uri, headers=headers, params=buy_order_details_data).json()

                                print(f"[WAITING TO EXECUTE] [{buy_order_details['submitted_at']}] "
                                      f"[{buy_order_details['status']}] {buy_order_details['side']} "
                                      f"order for {buy_order_details['qty']} shares of {buy_order_details['symbol']}")

                                if buy_order_details.status == 'filled':    # or order_details.status == 'partially_filled':
                                    buy_order_executed = True

                            ###############
                            buy_price = float(buy_order_details['filled_avg_price'])   # ACTUAL
                            ###############

                            filled_at = buy_order_details['filled_at']
                            filled_qty = buy_order_details['filled_qty']


                            print(f"[EXECUTED] [{filled_at}] {buy_order_details['side']} Order of {filled_qty} was executed @ {buy_price}")

                            signal = [filled_at, buy_price, 'g^',
                                  f'BUY@ {buy_price} [{filled_at}]']  # Buy at price 2 bars prior

                            signals.append(signal)

                            # TODO: [IMPORTANT] Use actual fill price to derive sell_target_based_on_profit_percentage

                            sell_target_based_on_profit_percentage = buy_price + (buy_price * profit_percentage)

                            print(f'[{np_cl_5m[-1]}] [{buy_price}] [{filled_at}]     '
                                  f'[BUY]       {BUY_SIGNAL}            '
                                  f'MOMENTUM    {bool_buy_momentum}          '
                                  f'POSITION    {position}             '
                                  f'CLOSING     {bool_closing_time}          '
                                  f'PROFIT_TARGET [{sell_target_based_on_profit_percentage}]        ')

                            position = True
                        else:
                            print(f"[ERROR] [{buy_order_details['filled_at']}] {buy_order_details['side']} Order was NOT placed")

                    ################### SELL ##################

                    elif position and SELL_SIGNAL:

                        sell_price = round(np_cl_5m[-2], 3)  # set sell price to 1 to 2 bars prior val
                        # for limit price, set sell_price

                        # https://docs.alpaca.markets/api-documentation/web-api/orders/

                        sell_order_data = {
                            'symbol': ticker,
                            'qty': config.units_to_trade,
                            'side': 'sell',
                            'type': 'market',
                            # 'limit_price': limit_price,
                            'time_in_force': 'day'
                            # 'client_order_id': uuid.uuid4().hex    # generate order_id e.g. '9fe2c4e93f654fdbb24c02b15259716c'
                        }
                        sell_order_data = json.dumps(sell_order_data)

                        print(f'SELL ORDER DATA:    {sell_order_data}')


                        sell_order_sent = False

                        try:
                            sell_order_placed = requests.post(url=order_uri, headers=headers, data=sell_order_data).json()
                            sell_order_sent = True
                            order_id = sell_order_placed['order_id']
                        except Exception as e:
                            print(f'Error placing order: {str(e)}')

                        sell_order_executed = False

                        print(f"SELL Order Placed Status Code:           {sell_order_placed['status_code']} ")

                        if sell_order_placed['status_code'] == 200:

                            while not sell_order_executed:

                                # keep checking until order is filled
                                sell_order_details_data = {'order_id': order_id}
                                sell_order_details = requests.get(url=order_uri, headers=headers, params=sell_order_details_data).json()

                                print(f'[WAITING TO EXECUTE] [{sell_order_details.submitted_at}] '
                                      f'[{sell_order_details.status}] {sell_order_details.side} '
                                      f'order for {sell_order_details.qty} shares of {sell_order_details.symbol}')

                                if sell_order_details.status == 'filled':    # or order_details.status == 'partially_filled':
                                    sell_order_executed = True

                            ###############
                            sell_price = float(buy_order_details.filled_avg_price)
                            ###############

                            filled_at = sell_order_details.filled_at

                            print(f'[EXECUTED] [{sell_order_details.filled_at}] {sell_order_details.side} Order was executed @ {sell_price}')

                            signal = [np_tl_5m[-1], sell_price, 'rv',
                                  f'SELL@{sell_price} [{np_tl_5m[-1]}]']  # Sell at price 2 bars prior

                        signals.append(signal)

                        profit = float(sell_price - buy_price) * units_to_trade

                        list_trade_pnl.append(profit)  # append to trade pnl

                        print(f'[{np_tl_5m[-1]}] [{sell_price}]     '
                              f'[SELL]      {SELL_SIGNAL}            '
                              f'MOMENTUM    {bool_sell_momentum}         '
                              f'POSITION    {position}              '
                              f'CLOSING     {bool_closing_time}          '
                              f'PROFIT_TARGET [{sell_target_based_on_profit_percentage}] {bool_sell_profit_target}  '
                              f'PRICE       {bool_sell_price}')

                        position = False  # set position to false once a sale has completed


                    # time.sleep(300)     # TODO: Double check if you need to sleep less or more

                    ############### 5 MIN ###############

                    ############### 1 MIN ###############

            elif bar_interval == 1:

                print(f'RUNNING 1 MIN BARS')

                bars = fetch_bars(bar_interval=bar_interval)  # 1 for 1Min, 5 for 5Min, 15 for 15Min

                np_cl_1m = bars['np_cl_1m']
                np_tl_1m = bars['np_tl_1m']

                # print(f'np_cl_1m:               {np_cl_1m}')
                # print(f'np_tl_1m:               {np_tl_1m}')

                # GET MOMENTUM
                mom_1m = talib.MOM(np_cl_1m, timeperiod=1)

                # print(f'mom_1m:               {mom_1m}')

                # TODO: Cancel order if not executed in 5 min (optional)

                signals = []

                BUY_PRICE = np.array([0.000])  # initialize here, set to actual avg price at which asset was bought

                sell_target_based_on_profit_percentage = np.array([0])  # initialization

                buy_price = 0.000  # float
                sell_price = 0.000  # float
                list_trade_profit = list()  # list to hold profit amount
                list_trade_pnl = list()  # dict to hold profit or loss for each trade
                day_pnl = 0.000  # for the day (float)

                trade_left_open = False  # to check if a trade was left open, initial False

                units_to_trade = config.units_to_trade
                # TODO: [IMPORTANT] derive units to trade dynamically based on cash balance and position size
                # TODO: handle partial fills (optional)

                ###########################

                # Profit percentage (price above buy price) 25% as 0.25, 10% as 0.1
                # used to set -> sell_target_based_on_profit_percentage

                profit_percentage = float(config.profit_percentage)  # 0.2 for 20%

                print(f'profit percentage                   {profit_percentage}')

                ###################     1 MIN BARS START    #######################

                # for i in range(len(np_cl_5m)):

                # STRATEGY 2: BUY if mom 2 > mom 1, SELL mom1, mom2 < 0 and current price > buy

                bool_closing_time = ts['market_about_to_close']
                bool_buy_momentum = (mom_1m[-1] > 0 and mom_1m[-2] > 0) and (mom_1m[-1] > mom_1m[-2])

                ################################

                BUY_SIGNAL = bool_buy_momentum  # and not bool_closing_time

                print(f'[{np_cl_1m[-1]}] BUY_SIGNAL                 {BUY_SIGNAL}')

                # TODO: [IMPORTANT] include closing time check in actual trades

                ################################

                bool_sell_momentum = mom_1m[-1] < 0 and mom_1m[-2] < 0  # current and prev momentum are positive

                bool_sell_price = float(np_cl_1m[-1]) > float(BUY_PRICE[0])  # current price is gt buy price
                # print(f'bool_sell_price [{bool_sell_price}] = float(np_cl_5m[i]) [{float(np_cl_5m[i])}] > float(BUY_PRICE[0]) [{float(BUY_PRICE[0])}]')

                bool_sell_profit_target = float(np_cl_1m[-1]) >= float(
                    sell_target_based_on_profit_percentage)  # current price > sell target
                # print(f'[{np_tl_5m[i]}] bool_sell_profit_target {bool_sell_profit_target} = float(np_cl_5m[i]) {float(np_cl_5m[i])} >= float(sell_target_based_on_profit_percentage) {float(sell_target_based_on_profit_percentage)}')

                # TODO: [IMPORTANT] don't use int, it drops the decimal places during comparison, use float instead

                ################################

                SELL_SIGNAL = (bool_sell_momentum and bool_sell_price) or \
                              bool_sell_profit_target  # or \
                # (bool_sell_price and position and bool_closing_time)  # TODO: Incorporate closing time

                print(f'[{np_cl_1m[-1]}] SELL_SIGNAL                {SELL_SIGNAL}')

                # print(f'[{np_tl_5m[i]}] [{round(np_cl_5m[i], 2)}]     '
                #       f'[SELL]      {SELL_SIGNAL}            '
                #       f'MOMENTUM    {bool_sell_momentum}          '
                #       f'POSITION    {position}              '
                #       f'CLOSING     {bool_closing_time}          '
                #       f'SELLPRICE     {bool_sell_price}          '
                #       f'PROFIT_TARGET [{sell_target_based_on_profit_percentage}] {bool_sell_profit_target}  ')

                ################################

                if np.isnan(mom_1m[-1]):
                    continue
                else:

                    ################### BUY ##################

                    if not position and BUY_SIGNAL:  # if no position exists and a buy sig is found

                        # TODO: check clock and don't buy 30 min before market close

                        BUY_PRICE[0] = float((np_cl_1m[-1] + np_cl_1m[-2]) / 2)  # for limit price only
                        buy_price = round(BUY_PRICE[0], 3)  # for limit price only

                        # limit_price = BUY_PRICE[0]

                        # https://docs.alpaca.markets/api-documentation/web-api/orders/

                        buy_order_data = {
                            'symbol': ticker,
                            'qty': config.units_to_trade,
                            'side': 'buy',
                            'type': 'market',
                            # 'limit_price': limit_price,
                            'time_in_force': 'day'
                            # 'client_order_id': uuid.uuid4().hex    # generate order_id e.g. '9fe2c4e93f654fdbb24c02b15259716c'
                        }
                        buy_order_data = json.dumps(buy_order_data)

                        print(f'BUY ORDER DATA:    {buy_order_data}')

                        buy_order_sent = False

                        try:
                            buy_order_placed = requests.post(url=order_uri, headers=headers,
                                                             data=buy_order_data).json()
                            buy_order_sent = True
                            order_id = buy_order_placed['id']
                        except Exception as e:
                            print(f'Error placing order: {str(e)}')

                        buy_order_executed = False

                        if buy_order_placed['status'] is not None:  # to check if order was placed

                            while not buy_order_executed:

                                # keep checking until order is filled
                                # buy_order_details_data = {'order_id': order_id}
                                # buy_order_details_data = json.dumps(buy_order_details_data)

                                get_order_details_uri = f'https://paper-api.alpaca.markets/v1/orders/{order_id}'

                                buy_order_details = requests.get(url=get_order_details_uri, headers=headers).json()

                                print(f"[WAITING TO EXECUTE] [{buy_order_details['submitted_at']}] "
                                      f"[{buy_order_details['status']}] {buy_order_details['side']} "
                                      f"order for {buy_order_details['qty']} shares of {buy_order_details['symbol']}")

                                if buy_order_details['status'] == 'filled':  # or order_details.status == 'partially_filled':
                                    buy_order_executed = True

                                print(f"Buy order status:           {buy_order_placed['status']} ")

                            ###############
                            buy_price = float(buy_order_details['filled_avg_price'])  # ACTUAL
                            ###############

                            filled_at = buy_order_details['filled_at']

                            print(f"[EXECUTED] [{filled_at}] {buy_order_details['side']} Order was executed @ {buy_price}")

                            signal = [filled_at, buy_price, 'g^',
                                      f'BUY@ {buy_price} [{filled_at}]']  # Buy at price 2 bars prior

                            signals.append(signal)

                            # TODO: [IMPORTANT] Use actual fill price to derive sell_target_based_on_profit_percentage

                            sell_target_based_on_profit_percentage = buy_price + (
                                        buy_price * profit_percentage)

                            print(f'[{np_cl_1m[-1]}] [{buy_price}] [{filled_at}]     '
                                  f'[BUY]       {BUY_SIGNAL}            '
                                  f'MOMENTUM    {bool_buy_momentum}          '
                                  f'POSITION    {position}             '
                                  f'CLOSING     {bool_closing_time}          '
                                  f'PROFIT_TARGET [{sell_target_based_on_profit_percentage}]        ')

                            position = True
                        else:
                            print(f"[ERROR] [{filled_at}] {buy_order_details['side']} Order was NOT placed")

                    ################### SELL ##################

                    elif position and SELL_SIGNAL:

                        sell_price = round(np_cl_1m[-2], 3)  # set sell price to 1 to 2 bars prior val
                        # for limit price, set sell_price

                        # https://docs.alpaca.markets/api-documentation/web-api/orders/

                        sell_order_data = {
                            'symbol': ticker,
                            'qty': config.units_to_trade,
                            'side': 'sell',
                            'type': 'market',
                            # 'limit_price': limit_price,
                            'time_in_force': 'day'
                            # 'client_order_id': uuid.uuid4().hex    # generate order_id e.g. '9fe2c4e93f654fdbb24c02b15259716c'
                        }
                        sell_order_data = json.dumps(sell_order_data)

                        print(f'SELL ORDER DATA:    {sell_order_data}')

                        sell_order_sent = False

                        try:
                            sell_order_placed = requests.post(url=order_uri, headers=headers,
                                                              data=sell_order_data).json()
                            sell_order_sent = True
                            order_id = sell_order_placed['id']
                        except Exception as e:
                            print(f'Error placing order: {str(e)}')

                        sell_order_executed = False

                        # print(f"SELL Order Placed Status Code:           {sell_order_placed['status_code']} ")

                        if sell_order_placed['status'] is not None:

                            while not sell_order_executed:

                                # keep checking until order is filled

                                get_order_details_uri = f'https://paper-api.alpaca.markets/v1/orders/{order_id}'

                                sell_order_details = requests.get(url=get_order_details_uri, headers=headers).json()

                                print(f"[WAITING TO EXECUTE SELL] [{sell_order_details['submitted_at']}] "
                                      f"[{sell_order_details['status']}] {sell_order_details['side']} "
                                      f"order for {sell_order_details['qty']} shares of {sell_order_details['symbol']}")

                                if sell_order_details['status'] == 'filled':  # or order_details.status == 'partially_filled':
                                    sell_order_executed = True

                                print(f"Sell order status:           {sell_order_placed['status']} ")

                            ###############
                            sell_price = float(buy_order_details['filled_avg_price'])
                            ###############

                            filled_at = sell_order_details['filled_at']
                            side = sell_order_details['side']
                            print(
                                f'[EXECUTED] [{filled_at}] {side} Order was executed @ {sell_price}')

                            signal = [np_tl_1m[-1], sell_price, 'rv',
                                      f'SELL@{sell_price} [{np_tl_1m[-1]}]']  # Sell at price 2 bars prior

                        signals.append(signal)

                        profit = float(sell_price - buy_price) * units_to_trade

                        list_trade_pnl.append(profit)  # append to trade pnl

                        print(f'[{np_tl_1m[-1]}] [{sell_price}]     '
                              f'[SELL]      {SELL_SIGNAL}            '
                              f'MOMENTUM    {bool_sell_momentum}         '
                              f'POSITION    {position}              '
                              f'CLOSING     {bool_closing_time}          '
                              f'PROFIT_TARGET [{sell_target_based_on_profit_percentage}] {bool_sell_profit_target}  '
                              f'PRICE       {bool_sell_price}')

                        position = False  # set position to false once a sale has completed

                        ############### 1 MIN ###############

                    # time.sleep(60)  # TODO: Double check if you need to sleep less or more

        if int(bar_interval) == 1:
            secs_to_sleep = 60
        elif int(bar_interval) == 5:
            secs_to_sleep = 300

        print('\n')
        print(f'WAITING {secs_to_sleep} SECONDS FOR THE NEXT BAR')
        print('\n')
        print('*'*80)
        print('\n')
        time.sleep(int(secs_to_sleep))


