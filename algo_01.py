# import alpaca_trade_api as tradeapi
import pandas as pd
import time
import logging
import config
import requests
import json
from datetime import datetime
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
    "APCA-API-SECRET-KEY": config.APCA_API_SECRET_KEY
}

# CHECK IF MARKET IS OPEN FOR TRADING

clock_uri = 'https://paper-api.alpaca.markets/v1/clock'
market_is_open = requests.get(url=clock_uri, headers=header).json()["is_open"]


# SET START AND END TIMES

now = pd.Timestamp.now(tz=NY)
# now = pd.Timestamp.now(tz=NY) - pd.Timedelta('180 Days ')  # FOR QA

end_time = now
# https://pandas.pydata.org/pandas-docs/stable/user_guide/timedeltas.html
# start_dt = end_dt - pd.Timedelta('5 days')  # 1 Minutes

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
    # "1D": "1D"
}

base_uri_1m = f'https://data.alpaca.markets/v1/bars/{bar_interval["1MIN"]}'
base_uri_5m = f'https://data.alpaca.markets/v1/bars/{bar_interval["5MIN"]}'
base_uri_15m = f'https://data.alpaca.markets/v1/bars/{bar_interval["15MIN"]}'
# base_uri_1d = f'https://data.alpaca.markets/v1/bars/{bar_interval["1D"]}'

tickers = ['MSFT']

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

# while market_is_open:


# positionSizing = 0.25

for ticker in tickers:

    limit = 15

    payload_1m = {
        "symbols": ticker,
        "limit": limit,
        "start": log_start_1m,
        "end": log_end_time
    }
    payload_5m = {
        "symbols": ticker,
        "limit": limit,
        "start": log_start_5m,
        "end": log_end_time
    }
    payload_15m = {
        "symbols": ticker,
        "limit": limit,
        "start": log_start_15m,
        "end": log_end_time
    }

    # print(f"BASE URI: {base_uri_1m}")

    bars_1m = requests.get(url=base_uri_1m, params=payload_1m, headers=header).json()
    bars_5m = requests.get(url=base_uri_5m, params=payload_5m, headers=header).json()
    bars_15m = requests.get(url=base_uri_15m, params=payload_15m, headers=header).json()


    # TODO: pull bars async
    # print(bars_1m)

    for i, (v1m, v5m, v15m) in enumerate(zip(bars_1m[ticker], bars_5m[ticker], bars_15m[ticker])):
    # for i, v15m in enumerate(bars_15m[ticker]):

        # calc per_change here

        # ts = bars_15m[ticker][i]['t']

        # CONVERT UNIX TS TO READABLE TS
        # ts_str=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(ts)))

        # APPEND TO LIST

        # append 1m bars to list
        ol_1m.append(v1m['o'])
        ll_1m.append(v1m['l'])
        hl_1m.append(v1m['h'])
        cl_1m.append(v1m['c'])
        vl_1m.append(v1m['v'])
        # tl_1m.append(v1m['t'])
        tl_1m.append(datetime.utcfromtimestamp(v1m['t']).strftime('%m%d%H%M'))

        # append 5m bars to list
        ol_5m.append(v5m['o'])
        ll_5m.append(v5m['l'])
        hl_5m.append(v5m['h'])
        cl_5m.append(v5m['c'])
        vl_5m.append(v5m['v'])
        # tl_5m.append(v5m['t'])
        tl_5m.append(datetime.utcfromtimestamp(v5m['t']).strftime('%m%d%H%M'))

        # append 5m bars to list
        ol_15m.append(v15m['o'])
        ll_15m.append(v15m['l'])
        hl_15m.append(v15m['h'])
        cl_15m.append(v15m['c'])
        vl_15m.append(v15m['v'])
        # tl_15m.append(v15m['t'])
        tl_15m.append(datetime.utcfromtimestamp(v15m['t']).strftime('%m%d%H%M'))    # TODO: CHECK IF TS is UTC?

        pass

    eta = datetime.now() - startTime

    print(f"[{datetime.now()}] Completed loading OHLCV LISTS")

    # CONVERT TO NP ARRAYS - OUTSIDE THE FOR

    # convert to 1m np array
    np_ol_1m = np.array(ol_1m)
    np_hl_1m = np.array(hl_1m)
    np_ll_1m = np.array(ll_1m)
    np_cl_1m = np.array(cl_1m)
    np_vl_1m = np.array(vl_1m)
    np_tl_1m = np.array(tl_1m)

    # convert to 5m np array
    np_ol_5m = np.array(ol_5m)
    np_hl_5m = np.array(hl_5m)
    np_ll_5m = np.array(ll_5m)
    np_cl_5m = np.array(cl_5m)
    np_vl_5m = np.array(vl_5m)
    np_tl_5m = np.array(tl_5m)

    # convert to 15m np array
    np_ol_15m = np.array(ol_15m)
    np_hl_15m = np.array(hl_15m)
    np_ll_15m = np.array(ll_15m)
    np_cl_15m = np.array(cl_15m)
    np_vl_15m = np.array(vl_15m)
    np_tl_15m = np.array(tl_15m)


    print(f"[{datetime.now()}] Completed loading OHLCV NP ARRARYS")

# MOMENTUM INDICATOR START

    # MOM = price - previous_price

    mom_1m = talib.MOM(np_cl_1m, timeperiod=1)
    mom_5m = talib.MOM(np_cl_5m, timeperiod=1)
    mom_15m = talib.MOM(np_cl_15m, timeperiod=1)


    print(f'MOM 1M: {mom_1m}')
    print(f'MOM 5M: {mom_5m}')
    print(f'MOM 15M: {mom_15m}')

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
    # ax1.title(f"MOM 1 Min Plot for {ticker}")
    # ax2.title(f"MOM 5 Min Plot for {ticker}")
    # ax3.title(f"MOM 15 Min Plot for {ticker}")

    # plt.title(f"MOM Plots for {ticker}")
    plt.xticks(rotation=90)
    plt.legend()
    plt.show()


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
            plt.plot(np_tl_15m, macdhist, label='MACD Histogram')
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
