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

clock_uri = 'https://paper-api.alpaca.markets/v1/clock'


def get_current_positions():

    positions_uri = f'https://paper-api.alpaca.markets/v1/positions/{ticker}'
    positions_response = requests.get(url=positions_uri, headers=headers).json()

    # {'asset_id': '4f5baf1e-0e9b-4d85-b88a-d874dc4a3c42',
    # 'symbol': 'V', 'exchange': 'NYSE',
    # 'asset_class': 'us_equity', 'qty': '10',
    # 'avg_entry_price': '144.17', 'side': 'long',
    # 'market_value': '1517.2', 'cost_basis': '1441.7',
    # 'unrealized_pl': '75.5', 'unrealized_plpc': '0.0523687313588125',
    # 'unrealized_intraday_pl': '10.5', 'unrealized_intraday_plpc': '0.0069688723700803',
    # 'current_price': '151.72',
    # 'lastday_price': '150.67',
    # 'change_today': '0.0069688723700803'}

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
    print(f'start_ts: {start_ts}')
    end_ts = ts['clock_ts']             # current ts
    print(f'end_ts: {end_ts}')
    market_close_ts = ts['close_ts']    # to prevent getting more bars after market has closed for the day
    print(f'market_close_ts: {market_close_ts}')


    # limit_5m = num_bars(start_ts=start_ts, end_ts=end_ts, market_close_ts=market_close_ts, num=5)

    limit_5m = 4

    print(f'limit_5m: {limit_5m}')

    bar_interval = "5Min"
    base_uri_5m = f'https://data.alpaca.markets/v1/bars/{bar_interval}'
    # print(f'base_uri_5m = {base_uri_5m}')

    payload_5m = {
        "symbols": ticker,
        "limit": limit_5m,
        "start": ts['log_start_5m'],
        "end": ts['log_end_time']
    }

    # print(f'payload_5m = {payload_5m}')

    bars_5m = requests.get(url=base_uri_5m, params=payload_5m, headers=headers).json()

    # print(f'bars_5m = {bars_5m}')

    # print(f'bars_5m[{ticker}] = {bars_5m[ticker]}')

    for i, v5m in enumerate(bars_5m[ticker]):
        # CONVERT UNIX TS TO READABLE TS
        v5m_ts_nyc = datetime.fromtimestamp(v5m['t']).astimezone(nyc)  # Covert Unix TS to NYC NOT UTC!!
        v5m_ts = v5m_ts_nyc.strftime('%Y-%m-%d %H:%M:%S')  # Convert to str with format

        # APPEND TO LIST

        ####    FOR DEBUGGING   ####

        # print('#########')
        # print(f"v5m['t']    {v5m['t']}")
        # print(f'v5m_ts_nyc  {v5m_ts_nyc}')
        # print(f'v5m_ts_tz   {v5m_ts}')
        # print('#########')

        ####    FOR DEBUGGING   ####

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

    print(f'np_tl_5m    {len(np_tl_5m)}  np_cl_5m    {len(np_cl_5m)}')


    bars_response = {
        "np_cl_5m": np_cl_5m,
        "np_tl_5m": np_tl_5m
    }

    return bars_response

# TODO: Add ETAs at each step


ticker = config.ticker

x = 0

while x < 3:  # infinite

    print('*'*80)
    print('\n')

    # Reset the lists each run to null
    tl_5m = list()
    ol_5m = list()
    hl_5m = list()
    ll_5m = list()
    cl_5m = list()
    vl_5m = list()

    # print(f'Entering x =        {x}')

    ts = get_ts()
    market_is_open = ts['is_open']  # check if market is open for trading
    print(f'market_is_open =    {market_is_open}')

    current_ts = ts['clock_ts']  # dup of end_ts, to be used for limiting past trades
    print(f'current_ts:         {current_ts}')

    if not market_is_open:

        # check if market just opened
        open_ts = ts['open_ts']

        next_trade_ts = current_ts + pd.Timedelta("5 Minutes")

        if current_ts.strftime('%Y-%m-%d %H:%M') == open_ts.strftime('%Y-%m-%d %H:%M'): # avoid comparing millisecs
            next_trade_ts = current_ts  # set next_trade_ts to current_ts if market just opened

        print(f'next_trade_ts:      {next_trade_ts}')

        if current_ts >= next_trade_ts:    # fetch the new price and time bar that's available
            # ready to trade

            # 0. Setup
            # Add positionSizing = 0.25 for each stock
            # cash_balance = get_cash_balance()

            # 1. check if a position exists from the previous trade

            positions = get_current_positions()
            # print(f'positions = {positions}')

            entry_price = positions['entry_price']  # avg price of buy for all units
            print(f'entry_price = {entry_price}')

            num_stocks_unsold = positions['num_stocks_unsold']   # length of the position dict
            print(f'num_stocks_unsold = {num_stocks_unsold}')

            position = False    # default position to False

            if num_stocks_unsold > 0:
                position = True    # TODO: replace with a function to check position

            print(f'position: {position}')

            # 2. get all timestamps

            current_ts = ts['clock_ts'] # dup of end_ts, to be used for limiting past trades
            print(f'current_ts: {current_ts}')

            next_trade_ts = current_ts  # first time as soon as market is open

            # to determine when to fetch bars and trade

            next_trade_ts = current_ts + pd.Timedelta("5 Minutes")
            print(f'next_trade_ts: {next_trade_ts}')


            # 3. fetch tickers based on current ts
            bar_interval = 5

            bars = fetch_bars(bar_interval=bar_interval)  # 1 for 1Min, 5 for 5Min, 15 for 15Min

            np_cl_5m = bars['np_cl_5m']
            np_tl_5m = bars['np_tl_5m']

            print(f'np_cl_5m: {np_cl_5m}')
            print(f'np_tl_5m: {np_tl_5m}')


            # now = datetime.now().astimezone(nyc).strftime('%Y-%m-%d %H:%M:%S')
            # print(f"[{now}] Completed loading OHLCV LISTS")

            # GET MOMENTUM
            mom_5m = talib.MOM(np_cl_5m, timeperiod=1)
            print(f'mom_5m: {mom_5m}')


            # STRATEGY 1 :

            # TODO: Cancel order if not executed in 5 mins??

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
            # TODO: handle partial fills

            ###########################

            # Profit percentage (price above buy price) 25% as 0.25, 10% as 0.1
            # used to set -> sell_target_based_on_profit_percentage

            profit_percentage = float(config.profit_percentage)  # 0.2 for 20%

            ###################     5 MIN BARS START    #######################

            for i in range(len(np_cl_5m)):

                # STRATEGY 2: BUY if mom 2 > mom 1, SELL mom1, mom2 < 0 and current price > buy

                bool_closing_time = ts['market_about_to_close']
                bool_buy_momentum = (mom_5m[i] > 0 and mom_5m[i - 1] > 0) and (mom_5m[i] > mom_5m[i - 1])

                ################################

                BUY_SIGNAL = bool_buy_momentum  # and not bool_closing_time

                # TODO: [IMPORTANT] include closing time check in actual trades

                ################################

                bool_sell_momentum = mom_5m[i] < 0 and mom_5m[i - 1] < 0  # current and prev momentum are positive

                bool_sell_price = float(np_cl_5m[i]) > float(BUY_PRICE[0])  # current price is gt buy price
                # print(f'bool_sell_price [{bool_sell_price}] = float(np_cl_5m[i]) [{float(np_cl_5m[i])}] > float(BUY_PRICE[0]) [{float(BUY_PRICE[0])}]')

                bool_sell_profit_target = float(np_cl_5m[i]) >= float(
                    sell_target_based_on_profit_percentage)  # current price > sell target
                # print(f'[{np_tl_5m[i]}] bool_sell_profit_target {bool_sell_profit_target} = float(np_cl_5m[i]) {float(np_cl_5m[i])} >= float(sell_target_based_on_profit_percentage) {float(sell_target_based_on_profit_percentage)}')

                # TODO: [IMPORTANT] don't use int, it drops the decimal places during comparison, use float instead

                ################################

                SELL_SIGNAL = (bool_sell_momentum and bool_sell_price) or \
                              bool_sell_profit_target  # or \
                # (bool_sell_price and position and bool_closing_time)  # TODO: Incorporate closing time

                # print(f'[{np_tl_5m[i]}] [{round(np_cl_5m[i], 2)}]     '
                #       f'[SELL]      {SELL_SIGNAL}            '
                #       f'MOMENTUM    {bool_sell_momentum}          '
                #       f'POSITION    {position}              '
                #       f'CLOSING     {bool_closing_time}          '
                #       f'SELLPRICE     {bool_sell_price}          '
                #       f'PROFIT_TARGET [{sell_target_based_on_profit_percentage}] {bool_sell_profit_target}  ')

                ################################

                if np.isnan(mom_5m[i]):
                    continue
                else:
                    if not position and BUY_SIGNAL:  # if no position exists and a buy sig is found

                        # TODO: check clock and don't buy 30 min before market close

                        BUY_PRICE[0] = float((np_cl_5m[i] + np_cl_5m[i - 1]) / 2)
                        buy_price = round(BUY_PRICE[0], 3)

                        signal = [np_tl_5m[i], buy_price, 'g^',
                                  f'BUY@ {buy_price} [{np_tl_5m[i]}]']  # Buy at price 2 bars prior
                        signals.append(signal)

                        # TODO: [IMPORTANT] Use actual fill price to derive sell_target_based_on_profit_percentage
                        sell_target_based_on_profit_percentage = BUY_PRICE[0] + (BUY_PRICE[0] * profit_percentage)

                        print(f'[{np_tl_5m[i]}] [{buy_price}]     '
                              f'[BUY]       {BUY_SIGNAL}            '
                              f'MOMENTUM    {bool_buy_momentum}          '
                              f'POSITION    {position}             '
                              f'CLOSING     {bool_closing_time}          '
                              f'PROFIT_TARGET [{sell_target_based_on_profit_percentage}]        ')

                        position = True

                    elif position and SELL_SIGNAL:

                        sell_price = round(np_cl_5m[i - 1], 3)  # set sell price to 1 to 2 bars prior val

                        signal = [np_tl_5m[i], sell_price, 'rv',
                                  f'SELL@{sell_price} [{np_tl_5m[i]}]']  # Sell at price 2 bars prior
                        signals.append(signal)

                        profit = float(sell_price - buy_price) * units_to_trade

                        list_trade_pnl.append(profit)  # append to trade pnl

                        print(f'[{np_tl_5m[i]}] [{sell_price}]     '
                              f'[SELL]      {SELL_SIGNAL}            '
                              f'MOMENTUM    {bool_sell_momentum}         '
                              f'POSITION    {position}              '
                              f'CLOSING     {bool_closing_time}          '
                              f'PROFIT_TARGET [{sell_target_based_on_profit_percentage}] {bool_sell_profit_target}  '
                              f'PRICE       {bool_sell_price}')

                        position = False  # set position to false once a sale has completed
        else:
            print('Waiting for the next bar')
    x = x+1
    # print(f'Exiting x=      {x}')
    print('\n')


        # if position:
        #     trade_left_open = True
        #
        # try:
        #     day_pnl = round(sum(list_trade_pnl), 2)
        # except Exception as e:
        #     largest_loss = 'NA'
        #
        # try:
        #     total_trades = len(list_trade_pnl)
        # except Exception as e:
        #     largest_loss = 'NA'
        #
        # try:
        #     wins = sum(n > 0 for n in list_trade_pnl)
        # except Exception as e:
        #     largest_loss = 'NA'
        #
        # try:
        #     losses = sum(n < 0 for n in list_trade_pnl)
        # except Exception as e:
        #     losses = 'NA'
        #
        # try:
        #     largest_profit = round(max(list_trade_pnl), 2)
        # except Exception as e:
        #     largest_profit = 'NA'
        #
        # try:
        #     largest_loss = min([n for n in list_trade_pnl if n < 0])
        # except Exception as e:
        #     largest_loss = 'NA'
        #
        # REF: https://stackoverflow.com/questions/27947941/retrieve-largest-negative-number-and-smallest-positive-number-from-list
        #
        # print('\n')
        # print("*" * 48)
        # print(f"SUMMARY FOR [{today_str}] \n")
        # print(f"Total PnL for the day           {day_pnl}")
        # print(f'Total trades placed             {total_trades}')
        # print(f'Wins                            {wins}')
        # print(f'Losses                          {losses}')
        # print(f'Largest Profit                  {largest_profit}')
        # print(f'Largest Loss                    {largest_loss}')
        # print(f'Trade Left Open                 {trade_left_open}')
        # print("*" * 48)

        # plt.plot(np_tl_5m, np_cl_5m, label='close', color='pink', linewidth=1, markersize=2, markerfacecolor='blue',
        #          marker='o')  # , linestyle='dashed')
        #
        # for signal in signals:
        #     plt.plot(signal[0], signal[1], signal[2], label=signal[3])
        #
        # plt.title(f"5 Min MOM Plot for {ticker}")
        # plt.xlabel("Time")
        # plt.ylabel("$ Value")
        # plt.legend()
        # plt.xticks(rotation=90)
        # plt.style.use('dark_background')
        # plt.grid(True)
        # plt.show()
