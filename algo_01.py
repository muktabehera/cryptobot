# import alpaca_trade_api as tradeapi
import pandas as pd
import time
import logging
import config
import requests
import json

from datetime import datetime
import pytz # for timezones
import dateutil.parser
# ref: https://medium.com/@eleroy/10-things-you-need-to-know-about-date-and-time-in-python-with-datetime-pytz-dateutil-timedelta-309bfbafb3f7

import numpy as np
import talib    # https://mrjbq7.github.io/ta-lib/
import matplotlib
matplotlib.use('TkAgg') # backend to use, valid strings are ['GTK3Agg', 'GTK3Cairo', 'MacOSX', 'nbAgg', 'Qt4Agg', 'Qt4Cairo', 'Qt5Agg', 'Qt5Cairo', 'TkAgg', 'TkCairo', 'WebAgg', 'WX', 'WXAgg', 'WXCairo', 'agg', 'cairo', 'pdf', 'pgf', 'ps', 'svg', 'template']

import matplotlib.pyplot as plt

# talib.get_functions()
# talib.get_function_groups()

startTime = datetime.now()

# SET LOGGING LEVEL
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


NY = 'America/New_York'

# api = tradeapi.REST(
#     key_id=config.APCA_API_KEY_ID,
#     secret_key=config.APCA_API_SECRET_KEY,
#     base_url=config.APCA_PAPER_BASE_URL
# )

header = {
    "APCA-API-KEY-ID": config.APCA_API_KEY_ID,
    "APCA-API-SECRET-KEY": config.APCA_API_SECRET_KEY,
    "Content-Type": "application/json"
}

# CHECK IF MARKET IS OPEN FOR TRADING

clock_uri = 'https://paper-api.alpaca.markets/v1/clock'

clock = requests.get(url=clock_uri, headers=header).json()
market_is_open = clock["is_open"]
next_open_ts = dateutil.parser.parse(clock['next_open'])
next_close_ts = dateutil.parser.parse(clock['next_close'])

clock_ts = dateutil.parser.parse(clock['timestamp'])

# SET START AND END TIMES

end_time = clock_ts
print(f'NOW: {clock_ts}, NEXT_OPEN: {next_open_ts}, NEXT_CLOSE: {next_close_ts}')

# Get when the market opens or opened today

nyc = pytz.timezone('America/New_York')
today = datetime.today().astimezone(nyc)
today_str = datetime.today().astimezone(nyc).strftime('%Y-%m-%d')
now = datetime.now().astimezone(nyc).strftime('%Y-%m-%d %H:%M:%S')

# https://pandas.pydata.org/pandas-docs/stable/user_guide/timedeltas.html

cal_uri = f"https://paper-api.alpaca.markets/v1/calendar?start={today.strftime('%Y-%m-%d')}&end={today.strftime('%Y-%m-%d')}"
cal = requests.get(cal_uri, headers=header).json()

open_ts = datetime.strptime(today.strftime('%Y-%m-%d') + ' ' + cal[0]['open'], '%Y-%m-%d %H:%M')
close_ts = datetime.strptime(today.strftime('%Y-%m-%d') + ' ' + cal[0]['close'], '%Y-%m-%d %H:%M')


closing_window = config.closing_window     # in Mins - > time in min left for market to close

about_to_close_ts = clock_ts - pd.Timedelta(f'{closing_window} Minutes')
market_about_to_close = False   # default market is not closing in the next 30 min

if clock_ts >= about_to_close_ts:
    market_about_to_close = True    # if there are 30 min left for market to close

print(f'market_about_to_close: {market_about_to_close} about_to_close_ts: {about_to_close_ts}')

print(f'OPEN: {open_ts} CLOSE: {close_ts}')

start_1m = end_time - pd.Timedelta('1 Minutes')
start_5m = end_time - pd.Timedelta('5 Minutes')
start_15m = end_time - pd.Timedelta('15 Minutes')
start_dt = end_time - pd.Timedelta('1 Days')

log_end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')       # 2019-03-04 02:05:58
log_end_dt = start_1m.strftime('%Y-%m-%d')                  # 2019-03-04
log_start_1m = start_1m.strftime('%Y-%m-%d %H:%M:%S')       # 2019-03-04 02:05:58
log_start_5m = start_5m.strftime('%Y-%m-%d %H:%M:%S')       # 2019-03-04 02:05:58
log_start_15m = start_15m.strftime('%Y-%m-%d %H:%M:%S')     # 2019-03-04 02:05:58
log_start_dt = start_dt.strftime('%Y-%m-%d')                # '2019-03-04'

# if market_is_open:
#     print('*' * 45)
#     print(f'[{log_end_time}] MARKET IS OPEN')
#     print('*' * 45)
#     print('\n')
# else:
#     pass


# Fetch last 10 > 1min, 5min, 15min, and daily bars
# bar_interval = ['1M', '5M', '15M', '1D']

bar_interval = {
    "1MIN": "1Min",
    "5MIN": "5Min",
    "15MIN": "15Min",
    "1D": "1D"
}

base_uri_1m = f'https://data.alpaca.markets/v1/bars/{bar_interval["1MIN"]}'
base_uri_5m = f'https://data.alpaca.markets/v1/bars/{bar_interval["5MIN"]}'
base_uri_15m = f'https://data.alpaca.markets/v1/bars/{bar_interval["15MIN"]}'
# base_uri_1d = f'https://data.alpaca.markets/v1/bars/{bar_interval["1D"]}'

tl_1m = list()  # time
ol_1m = list()  # open
hl_1m = list()  # high
ll_1m = list()  # low
cl_1m = list()  # close
vl_1m = list()  # vol

tl_5m = list()
ol_5m = list()
hl_5m = list()
ll_5m = list()
cl_5m = list()
vl_5m = list()

tl_15m = list()
ol_15m = list()
hl_15m = list()
ll_15m = list()
cl_15m = list()
vl_15m = list()


ts_str = ''


# TODO: implement a check for clock['is_open'] --> MARKET IS OPEN

# TODO: Add positionSizing = 0.25 for each stock

tickers = config.tickers

for ticker in tickers:

    limit_1m = config.limit_1m # 78 * 5
    limit_5m = config.limit_5m   # 78 bars in a regular trading day 9.30 AM - 3:55 PM
    limit_15m = config.limit_15m  # 78 / 3

    payload_1m = {
        "symbols": ticker,
        "limit": limit_1m,
        "start": log_start_1m,
        "end": log_end_time
    }
    payload_5m = {
        "symbols": ticker,
        "limit": limit_5m,
        "start": log_start_5m,
        "end": log_end_time
    }
    payload_15m = {
        "symbols": ticker,
        "limit": limit_15m,
        "start": log_start_15m,
        "end": log_end_time
    }

    # print(f"BASE URI: {base_uri_1m}")

    bars_1m = requests.get(url=base_uri_1m, params=payload_1m, headers=header).json()
    bars_5m = requests.get(url=base_uri_5m, params=payload_5m, headers=header).json()
    bars_15m = requests.get(url=base_uri_15m, params=payload_15m, headers=header).json()


    # TODO: pull bars async
    # print(bars_1m)

    for i, v1m in enumerate(bars_1m[ticker]):

        # CONVERT UNIX TS TO READABLE TS
        v1m_ts_nyc = datetime.fromtimestamp(v1m['t']).astimezone(nyc)  # Covert Unix TS to NYC NOT UTC!!
        v1m_ts = v1m_ts_nyc.strftime('%Y-%m-%d %H:%M:%S')  # Convert to str with format

        # APPEND TO LIST

        # append 1m bars to list
        ol_1m.append(v1m['o'])
        ll_1m.append(v1m['l'])
        hl_1m.append(v1m['h'])
        cl_1m.append(v1m['c'])
        vl_1m.append(v1m['v'])

        tl_1m.append(v1m_ts)

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

    for i, v15m in enumerate(bars_15m[ticker]):

        # CONVERT UNIX TS TO READABLE TS
        v15m_ts_nyc = datetime.fromtimestamp(v15m['t']).astimezone(nyc)  # Covert Unix TS to NYC NOT UTC!!
        v15m_ts = v15m_ts_nyc.strftime('%Y-%m-%d %H:%M:%S')  # Convert to str with format

        # APPEND TO LIST

        # append 15m bars to list
        ol_15m.append(v15m['o'])
        ll_15m.append(v15m['l'])
        hl_15m.append(v15m['h'])
        cl_15m.append(v15m['c'])
        vl_15m.append(v15m['v'])

        tl_15m.append(v15m_ts)

    # TODO: REMOVE zip and pull bars separately by time window
    # [NOTE] Zipping causes limits to not work, all limits are reduced to 15min limit (or lower limit of all 3 lists)

    ''' 
    for i, (v1m, v5m, v15m) in enumerate(zip(bars_1m[ticker], bars_5m[ticker], bars_15m[ticker])):

        # CONVERT UNIX TS TO READABLE TS

        v1m_ts_nyc = datetime.fromtimestamp(v1m['t']).astimezone(nyc)        # Covert Unix TS to NYC NOT UTC!!
        v1m_ts = v1m_ts_nyc.strftime('%Y-%m-%d %H:%M:%S')                    # Convert to str with format

        v5m_ts_nyc = datetime.fromtimestamp(v5m['t']).astimezone(nyc)
        v5m_ts = v5m_ts_nyc.strftime('%Y-%m-%d %H:%M:%S')

        ####    FOR DEBUGGING   ####
        
        # print('#########')
        # print(f"v5m['t']    {v5m['t']}")
        # print(f'v5m_ts_nyc  {v5m_ts_nyc}')
        # print(f'v5m_ts_tz   {v5m_ts}')
        # print('#########')
        
        ####    FOR DEBUGGING   ####
        
        v15m_ts_nyc = datetime.fromtimestamp(v15m['t']).astimezone(nyc)
        v15m_ts = v5m_ts_nyc.strftime('%Y-%m-%d %H:%M:%S')


        # APPEND TO LIST

        # append 1m bars to list
        ol_1m.append(v1m['o'])
        ll_1m.append(v1m['l'])
        hl_1m.append(v1m['h'])
        cl_1m.append(v1m['c'])
        vl_1m.append(v1m['v'])

        tl_1m.append(v1m_ts)

        # append 5m bars to list
        ol_5m.append(v5m['o'])
        ll_5m.append(v5m['l'])
        hl_5m.append(v5m['h'])
        cl_5m.append(v5m['c'])
        vl_5m.append(v5m['v'])

        tl_5m.append(v5m_ts)

        # append 5m bars to list
        ol_15m.append(v15m['o'])
        ll_15m.append(v15m['l'])
        hl_15m.append(v15m['h'])
        cl_15m.append(v15m['c'])
        vl_15m.append(v15m['v'])

        tl_15m.append(v15m_ts)

        pass
    '''

    # TODO: Add ETAs at each step

    now = datetime.now().astimezone(nyc).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] Completed loading OHLCV LISTS")

    # CONVERT TO NP ARRAYS - OUTSIDE THE FOR

    # convert to 1m np array
    np_ol_1m = np.array(ol_1m)
    np_hl_1m = np.array(hl_1m)
    np_ll_1m = np.array(ll_1m)
    np_cl_1m = np.array(cl_1m)
    np_vl_1m = np.array(vl_1m)
    np_tl_1m = np.array(tl_1m)[:limit_1m]   # TODO: Remove redundant check

    print(f'np_tl_1m    {len(np_tl_1m)}  np_cl_1m    {len(np_cl_1m)}')

    # convert to 5m np array
    np_ol_5m = np.array(ol_5m)
    np_hl_5m = np.array(hl_5m)
    np_ll_5m = np.array(ll_5m)
    np_cl_5m = np.array(cl_5m)
    np_vl_5m = np.array(vl_5m)
    np_tl_5m = np.array(tl_5m)

    print(f'np_tl_5m    {len(np_tl_5m)}  np_cl_5m    {len(np_cl_5m)}')

    # convert to 15m np array
    np_ol_15m = np.array(ol_15m)
    np_hl_15m = np.array(hl_15m)
    np_ll_15m = np.array(ll_15m)
    np_cl_15m = np.array(cl_15m)
    np_vl_15m = np.array(vl_15m)
    np_tl_15m = np.array(tl_15m)

    print(f'np_tl_15m    {len(np_tl_15m)}  np_cl_15m    {len(np_cl_15m)}')

    now = datetime.now().astimezone(nyc).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] Completed loading OHLCV NP ARRARYS \n")

# MOMENTUM INDICATOR START

    # MOM = price - previous_price

    mom_1m = talib.MOM(np_cl_1m, timeperiod=1)
    mom_5m = talib.MOM(np_cl_5m, timeperiod=1)
    mom_15m = talib.MOM(np_cl_15m, timeperiod=1)

    # STRATEGY 1 :
    #   Buy when 3 mom bars are +ve
    #   Sell after next 3 bars
    #   Only buy->sell, not sell->buy

    # TODO: Cancel order if not executed in 5 mins??

    signals = []

    position = False
    BUY_PRICE = np.array([0.000])   # initialization
    sell_target_based_on_profit_percentage = np.array([0])  # initialization

    buy_price = 0.000       # float
    sell_price = 0.000      # float
    list_trade_profit = list()  # list to hold profit amount
    list_trade_pnl = list()      # dict to hold profit or loss for each trade
    day_pnl = 0.000         # for the day (float)

    trade_left_open = False     # to check if a trade was left open, initial False

    units_to_trade = config.units_to_trade
    # TODO: [IMPORTANT] derive units to trade dynamically based on cash balance and position size
    # TODO: handle partial fills

    ###########################

    # Profit percentage (price above buy price) 25% as 0.25, 10% as 0.1
    # used to set -> sell_target_based_on_profit_percentage

    profit_percentage = float(config.profit_percentage)   # 0.2 for 20%

    ###########################

    # TODO: Add a var window_small = '1m'

    ###################     1 MIN BARS START    #######################
    '''
    for i in range(len(np_cl_1m)):

        # STRATEGY 2: BUY if mom 2 > mom 1, SELL mom1, mom2 < 0 and current price > buy

        bool_closing_time = market_about_to_close
        bool_buy_momentum = (mom_1m[i] > 0 and mom_1m[i-1] > 0) and (mom_1m[i] > mom_1m[i-1])

        ################################

        BUY_SIGNAL = bool_buy_momentum # and not bool_closing_time

        # TODO: [IMPORTANT] include closing time check in actual trades

        ################################

        bool_sell_momentum = mom_1m[i] < 0 and mom_1m[i-1] < 0                                          # current and prev momentum are positive
        bool_sell_price = float(np_cl_1m[i]) > float(BUY_PRICE[0])                                      # current price is gt buy price
        # print(f'bool_sell_price [{bool_sell_price}] = float(np_cl_1m[i]) [{float(np_cl_1m[i])}] > float(BUY_PRICE[0]) [{float(BUY_PRICE[0])}]')

        bool_sell_profit_target = float(np_cl_1m[i]) >= float(sell_target_based_on_profit_percentage)   # current price > sell target

        # TODO: [IMPORTANT] don't use int, it drops the decimal places during comparison, use float instead

        ################################

        SELL_SIGNAL = (bool_sell_momentum and bool_sell_price) or \
                      bool_sell_profit_target #or \
                      #(bool_sell_price and position and bool_closing_time)  # TODO: Incorporate closing time

        # print(f'[{np_tl_1m[i]}] [{round(np_cl_1m[i], 2)}]     '
        #       f'[SELL]      {SELL_SIGNAL}            '
        #       f'MOMENTUM    {bool_sell_momentum}          '
        #       f'POSITION    {position}              '
        #       f'CLOSING     {bool_closing_time}          '
        #       f'SELLPRICE     {bool_sell_price}          '
        #       f'PROFIT_TARGET [{sell_target_based_on_profit_percentage}] {bool_sell_profit_target}  ')


        ################################

        if np.isnan(mom_1m[i]):
            continue
        else:
            if not position and BUY_SIGNAL:     # if no position exists and a buy sig is found

                # TODO: check clock and don't buy 30 min before market close

                signal = [np_tl_1m[i], np_cl_1m[i], 'g^', f'BUY@ {np_cl_1m[i]} [{np_tl_1m[i]}]']  # Buy at price 2 bars prior
                signals.append(signal)
                BUY_PRICE[0] = float(np_cl_1m[i])

                # TODO: [IMPORTANT] Use actual fill price to derive sell_target_based_on_profit_percentage
                sell_target_based_on_profit_percentage = BUY_PRICE[0] + (BUY_PRICE[0] * profit_percentage)

                print(f'[{np_tl_1m[i]}] [{round(np_cl_1m[i], 2)}]     '
                      f'[BUY]       {BUY_SIGNAL}            '
                      f'MOMENTUM    {bool_buy_momentum}          '
                      f'POSITION    {position}             '
                      f'CLOSING     {bool_closing_time}          '
                      f'PROFIT_TARGET [{sell_target_based_on_profit_percentage}]        ')

                position = True

            elif position and SELL_SIGNAL:
                signal = [np_tl_1m[i], np_cl_1m[i], 'rv', f'SELL@{np_cl_1m[i]} [{np_tl_1m[i]}]']   # Sell at price 2 bars prior
                signals.append(signal)

                print(f'[{np_tl_1m[i]}] [{round(np_cl_1m[i], 2)}]     '
                      f'[SELL]      {SELL_SIGNAL}            '
                      f'MOMENTUM    {bool_sell_momentum}         '
                      f'POSITION    {position}              '
                      f'CLOSING     {bool_closing_time}          '
                      f'PROFIT_TARGET [{sell_target_based_on_profit_percentage}] {bool_sell_profit_target}  '
                      f'PRICE       {bool_sell_price}')

                position = False

    # plt.plot(np_tl_15m, mom_1m, label='MOM 1Min')
    plt.plot(np_tl_1m, np_cl_1m, label='close', color='pink', linewidth=1, markersize=2, markerfacecolor='blue',
             marker='o') #, linestyle='dashed')

    for signal in signals:
        plt.plot(signal[0], signal[1], signal[2], label=signal[3])

    plt.title(f"1 Min MOM Plot for {ticker}")
    plt.xlabel("Time")
    plt.ylabel("$ Value")
    plt.legend()
    plt.xticks(rotation=90)
    plt.style.use('dark_background')
    plt.show()
    '''
    ###################     1 MIN BARS END    #########################


    ###################     5 MIN BARS START    #######################

    for i in range(len(np_cl_5m)):

        # STRATEGY 2: BUY if mom 2 > mom 1, SELL mom1, mom2 < 0 and current price > buy

        bool_closing_time = market_about_to_close
        bool_buy_momentum = (mom_5m[i] > 0 and mom_5m[i-1] > 0) and (mom_5m[i] > mom_5m[i-1])

        ################################

        BUY_SIGNAL = bool_buy_momentum # and not bool_closing_time

        # TODO: [IMPORTANT] include closing time check in actual trades

        ################################

        bool_sell_momentum = mom_5m[i] < 0 and mom_5m[i-1] < 0                                          # current and prev momentum are positive
        bool_sell_price = float(np_cl_5m[i]) > float(BUY_PRICE[0])                                      # current price is gt buy price
        # print(f'bool_sell_price [{bool_sell_price}] = float(np_cl_5m[i]) [{float(np_cl_5m[i])}] > float(BUY_PRICE[0]) [{float(BUY_PRICE[0])}]')

        bool_sell_profit_target = float(np_cl_5m[i]) >= float(sell_target_based_on_profit_percentage)   # current price > sell target
        # print(f'[{np_tl_5m[i]}] bool_sell_profit_target {bool_sell_profit_target} = float(np_cl_5m[i]) {float(np_cl_5m[i])} >= float(sell_target_based_on_profit_percentage) {float(sell_target_based_on_profit_percentage)}')

        # TODO: [IMPORTANT] don't use int, it drops the decimal places during comparison, use float instead

        ################################

        SELL_SIGNAL = (bool_sell_momentum and bool_sell_price) or \
                      bool_sell_profit_target #or \
                      #(bool_sell_price and position and bool_closing_time)  # TODO: Incorporate closing time

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
            if not position and BUY_SIGNAL:     # if no position exists and a buy sig is found

                # TODO: check clock and don't buy 30 min before market close

                BUY_PRICE[0] = float((np_cl_5m[i] + np_cl_5m[i - 1]) / 2)
                buy_price = round(BUY_PRICE[0],3)

                signal = [np_tl_5m[i], buy_price, 'g^', f'BUY@ {buy_price} [{np_tl_5m[i]}]']  # Buy at price 2 bars prior
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

                sell_price = round(np_cl_5m[i-1], 3)  # set sell price to 1 to 2 bars prior val

                signal = [np_tl_5m[i], sell_price, 'rv', f'SELL@{sell_price} [{np_tl_5m[i]}]']   # Sell at price 2 bars prior
                signals.append(signal)

                profit = float(sell_price - buy_price) * units_to_trade

                list_trade_pnl.append(profit)            # append to trade pnl

                print(f'[{np_tl_5m[i]}] [{sell_price}]     '
                      f'[SELL]      {SELL_SIGNAL}            '
                      f'MOMENTUM    {bool_sell_momentum}         '
                      f'POSITION    {position}              '
                      f'CLOSING     {bool_closing_time}          '
                      f'PROFIT_TARGET [{sell_target_based_on_profit_percentage}] {bool_sell_profit_target}  '
                      f'PRICE       {bool_sell_price}')

                position = False        # set position to false once a sale has completed

    if position:
        trade_left_open = True

    day_pnl = round(sum(list_trade_pnl),2)
    total_trades = len(list_trade_pnl)
    wins = sum(n > 0 for n in list_trade_pnl)
    loses = sum(n < 0 for n in list_trade_pnl)
    largest_profit = round(max(list_trade_pnl),2)

    try:
        largest_loss = min([n for n in list_trade_pnl if n < 0])
    except Exception as e:
        largest_loss = 'NA'

    # REF: https://stackoverflow.com/questions/27947941/retrieve-largest-negative-number-and-smallest-positive-number-from-list

    print('\n')
    print("*" * 48)
    print(f"SUMMARY FOR [{today_str}] \n")
    print(f"Total PnL for the day           {day_pnl}")
    print(f'Total trades placed             {total_trades}')
    print(f'Wins                            {wins}')
    print(f'Losses                          {loses}')
    print(f'Largest Profit                  {largest_profit}')
    print(f'Largest Loss                    {largest_loss}')
    print(f'Trade Left Open                 {trade_left_open}')
    print("*" * 48)

    plt.plot(np_tl_5m, np_cl_5m, label='close', color='pink', linewidth=1, markersize=2, markerfacecolor='blue',
             marker='o') #, linestyle='dashed')

    for signal in signals:
        plt.plot(signal[0], signal[1], signal[2], label=signal[3])

    plt.title(f"5 Min MOM Plot for {ticker}")
    plt.xlabel("Time")
    plt.ylabel("$ Value")
    plt.legend()
    plt.xticks(rotation=90)
    plt.style.use('dark_background')
    plt.grid(True)
    plt.show()

    ###################     5 MIN BARS END    #########################


# THREE MOM SUBPLOTS START
'''
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharey=True)

    ax1.set_ylabel('$ value')

    ax1.set_xlabel('time (1m)')
    ax2.set_xlabel('time (5m)')
    ax2.set_xlabel('time (15m)')

    # plt.style.use('dark_background')
    ax1.plot(np_tl_1m, mom_1m, label='MOM-1Min')
    ax2.plot(np_tl_5m, mom_5m, label='MOM-5Min')
    ax3.plot(np_tl_15m, mom_15m, label='MOM-15Min')

    # for cross in crosses:
    #     plt.plot(cross[0], cross[1], cross[2])
    #         plt.plot(np_tl_15m, macdhist, label='MACD Histogram')
    ax1.set_title(f"MOM 1 Min Plot for {ticker}")
    ax2.set_title(f"MOM 5 Min Plot for {ticker}")
    ax3.set_title(f"MOM 15 Min Plot for {ticker}")

    # plt.title(f"MOM Plots for {ticker}")
    plt.xticks(rotation=90)
    plt.legend()
    plt.show()
'''

# MACD SIGNAL CROSS START #########
'''
    fastperiod = 12
    slowperiod = 26
    signalperiod = 9

    macd, macdsignal, macdhist = talib.MACD(np_cl_15m, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)

    crosses = []
    macdabove = False
    for i in range(len(macd)):
        if np.isnan(macd[i]) or np.isnan(macdsignal[i]):
            pass
        else:
            if macd[i] > macdsignal[i]:
                if macdabove == False:
                    macdabove = True
                    cross = [np_tl_15m[i], macd[i], 'go']
                    crosses.append(cross)
            else:
                if macdabove == True:
                    macdabove = False
                    cross = [np_tl_15m[i], macd[i], 'ro']
                    crosses.append(cross)

    plt.style.use('dark_background')
    plt.plot(np_tl_15m, macd, label='MACD 15Min')
    plt.plot(np_tl_15m, macdsignal, label='MACD Signal')
    for cross in crosses:
        plt.plot(cross[0], cross[1], cross[2])
            # plt.plot(np_tl_15m, macdhist, label='MACD Histogram')
    plt.title(f"MACD Plot for {ticker}")
    plt.xlabel("Open Time")
    plt.ylabel("Value")
    plt.legend()
    plt.show()
'''
# MACD SIGNAL CROSS END #########

# SMA CROSS OVER START
'''
    fastma = 5
    slowma = 10

    SMA3 = talib.SMA(np_cl_15m, fastma)[-1]     # -1 to get the last/latest SMA val
    SMA9 = talib.SMA(np_cl_15m, slowma)[-1]     # -1 to get the last/latest SMA val


    # CHECK OPEN POSITIONS:
    account_url = 'https://paper-api.alpaca.markets/v1/account'
    position_url = f'https://paper-api.alpaca.markets/v1/positions/{ticker}'

    account = requests.get(url=account_url, headers=header).json()
    positions = requests.get(url=position_url, headers=header).json()

    status = account['status']
    buying_power = account['buying_power']
    position_exists = len(positions)    # i.e. have one of more active positions

    BUY_SIGNAL = SMA3 > SMA9
    SELL_SIGNAL = SMA3 < SMA9

    if not position_exists:
        # TODO: if no open positions, set position size == cashBalance / (price / positionSizing)

        if BUY_SIGNAL:
            # place a limit buy order
            print(f'[{log_end_time}] BUY MKT @ {np_cl_15m[-1]}')

    else:   # i.e. position exists (we only sell if a position exists.

            if SELL_SIGNAL:
                print(f'[{log_end_time}] SELL MKT @ {np_ol_15m[-1]}')
                # place a limit sell order
'''
# SMA CROSS OVER START
# SMA CROSS OVER PLOTTING START
'''
    SMA3 = talib.SMA(np_cl_15m, fastma)  # -1 to get the last/latest SMA val
    SMA9 = talib.SMA(np_cl_15m, slowma) # -1 to get the last/latest SMA val
    crosses = []
    sma3above = False
    for i in range(len(np_tl_15m)):
        if np.isnan(SMA3[i]) or np.isnan(SMA9[i]):
            continue
        else:
            if SMA3[i] > SMA9[i]:
                if not sma3above:
                    sma3above = True
                    # cross = [np_tl_15m[i], np_cl_15m[i], 'g^']   # use np_cl_15m[i] instead of SMA3[i] for buy price
                    cross = [np_tl_15m[i], SMA3[i], 'g^']
                    crosses.append(cross)
            else:
                if sma3above:
                    sma3above = False
                    cross = [np_tl_15m[i], np_cl_15m[i], 'rv'] # red down arrow, use np_cl_15m[i] instead of SMA3[i]
                    # TODO: Add BUY / SELL text if possible
                    # Ref - https://matplotlib.org/api/markers_api.html
                    crosses.append(cross)
    #
    # plt.style.use('dark_background')
    plt.plot(np_tl_15m, SMA3, label='SMA3')
    plt.plot(np_tl_15m, SMA9, label='SMA9')
    plt.plot(np_tl_15m, np_cl_15m, label='close', color='magenta', linewidth=1, markersize=2, markerfacecolor='blue',
             marker='o', linestyle='dashed')
    
    for cross in crosses:
        plt.plot(cross[0], cross[1], cross[2])
        
    plt.title(f"15mSMA{fastma}-{slowma} CROSSOVER Plot for {ticker}")
    plt.xlabel("Time")
    plt.xticks(rotation=90)
    plt.ylabel("Value")
    plt.legend()
    plt.show()
'''
# SMA CROSS OVER PLOTTING END




    # output = talib.MOM(np_cl, timeperiod=1)
    # output = talib.ROCP(np_cl, timeperiod=1)
