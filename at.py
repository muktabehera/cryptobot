# TODO: Add Exception handling (Connection Error, etc)

# import alpaca_trade_api as tradeapi
import pandas as pd
import time
import logging
import config
import requests
import json
import argparse

from datetime import datetime
import pytz  # for timezones
import dateutil.parser
# ref: https://medium.com/@eleroy/10-things-you-need-to-know-about-date-and-time-in-python-with-datetime-pytz-dateutil-timedelta-309bfbafb3f7

import numpy as np
import talib  # https://mrjbq7.github.io/ta-lib/

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

    clock_uri = config.clock_uri
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

    prev_dt = today_ts - pd.Timedelta('1 Days')
    prev_dt_str = prev_dt.strftime('%Y-%m-%d')

    # https://pandas.pydata.org/pandas-docs/stable/user_guide/timedeltas.html

    cal_uri = f"{config.base_url}/calendar?start={today_ts.strftime('%Y-%m-%d')}&end={today_ts.strftime('%Y-%m-%d')}"
    cal = requests.get(cal_uri, headers=headers).json()

    open_ts_pst = dateutil.parser.parse(today_ts.strftime('%Y-%m-%d') + ' ' + cal[0]['open']) - pd.Timedelta("180 Minutes")
    # to make it tz aware for num_bars calculation
    open_ts_nyc = open_ts_pst.astimezone(nyc)
    open_ts = open_ts_nyc

    open_ts_30m = open_ts + pd.Timedelta('30 Minutes')
    open_ts_30m_str = open_ts_30m.strftime('%Y-%m-%d %H:%M:%S')

    open_ts_str = datetime.strptime(today_ts.strftime('%Y-%m-%d') + ' ' + cal[0]['open'], '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M:%S')

    close_ts_pst = dateutil.parser.parse(today_ts.strftime('%Y-%m-%d') + ' ' + cal[0]['close']) - pd.Timedelta("180 Minutes")
    close_ts_nyc = close_ts_pst.astimezone(nyc)
    close_ts = close_ts_nyc

    close_ts_str = datetime.strptime(today_ts.strftime('%Y-%m-%d') + ' ' + cal[0]['close'], '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M:%S')

    closing_window = config.closing_window  # in Mins - > time in min left for market to close
    about_to_close_ts = close_ts - pd.Timedelta(f'{closing_window} Minutes')
    # current_timestamp + 60 mins

    market_about_to_close = False  # default market is not closing in the next 30 min

    if clock_ts >= about_to_close_ts:
        market_about_to_close = True  # if there are 30 min left for market to close

    # start_1m = end_time - pd.Timedelta('1 Minutes')
    # start_5m = end_time - pd.Timedelta('5 Minutes')
    # start_15m = end_time - pd.Timedelta('15 Minutes')




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

        "prev_dt_str": prev_dt_str,
        "open_ts_str": open_ts_str,
        "open_ts_30m_str": open_ts_30m_str

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

'''
def fetch_bars(data_provider):       # data_provider = config.data_provider

    np_hl_1m = np.array([])
    np_ll_1m = np.array([])
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
            "symbols": ticker,
            "limit": limit_1m
            # "start": ts['log_start_1m'],
            # "end": ts['log_end_time']
        }
        base_uri_1m = f'{config.data_url}/bars/{bar_interval}'
        bars_1m = requests.get(url=base_uri_1m, params=payload_1m, headers=headers).json()

        for i, v1m in enumerate(bars_1m[ticker]):
            # CONVERT UNIX TS TO READABLE TS
            v1m_ts_nyc = datetime.fromtimestamp(v1m['t']).astimezone(nyc)  # Covert Unix TS to NYC NOT UTC!!
            v1m_ts = v1m_ts_nyc.strftime('%Y-%m-%d %H:%M:%S')  # Convert to str with format

            # APPEND TO LIST

            # append 1m bars to list
            # ol_1m.append(v1m['o'])
            ll_1m.append(v1m['l'])
            hl_1m.append(v1m['h'])
            cl_1m.append(v1m['c'])
            # vl_1m.append(v1m['v'])
            tl_1m.append(v1m_ts)
            # float_tl_1m.append(v1m['t'])  # to get float ts for linear regression

            # convert to 1m np array
            # added datatype float to avoid real is not double error during MOM cacl
            # np_ol_1m = np.array(ol_1m, dtype=float)
            np_hl_1m = np.array(hl_1m, dtype=float)
            np_ll_1m = np.array(ll_1m, dtype=float)
            np_cl_1m = np.array(cl_1m, dtype=float)
            # np_vl_1m = np.array(vl_1m, dtype=float)
            np_tl_1m = np.array(tl_1m)
            # float_np_tl_1m = np.array(float_tl_1m, dtype=float)

            # round to 2 decimal places

            # np_ol_1m = np.round(np_ol_1m, 2)
            np_hl_1m = np.round(np_hl_1m, 2)
            np_ll_1m = np.round(np_ll_1m, 2)
            np_cl_1m = np.round(np_cl_1m, 2)
            # np_vl_1m = np.round(np_vl_1m, 2)

            # no need to round of time np arrays

        # logging.info(f'np_tl_1m    {len(np_tl_1m)}  np_cl_1m    {len(np_cl_1m)}')

        bars_response = {

            # "np_ol_1m": np_ol_1m,
            "np_hl_1m": np_hl_1m,
            "np_ll_1m": np_ll_1m,
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
        base_uri_1m = f'{config.data_url}/{bar_interval}/{ticker}'

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
            ll_1m.append(v1m['l'])
            hl_1m.append(v1m['h'])
            cl_1m.append(v1m['c'])
            # vl_1m.append(v1m['v'])
            tl_1m.append(v1m_ts)
            # float_tl_1m.append(v1m['t'])  # to get float ts for linear regression

            # convert to 1m np array
            # added datatype float to avoid real is not double error during MOM cacl
            # np_ol_1m = np.array(ol_1m, dtype=float)
            np_hl_1m = np.array(hl_1m, dtype=float)
            np_ll_1m = np.array(ll_1m, dtype=float)
            np_cl_1m = np.array(cl_1m, dtype=float)
            # np_vl_1m = np.array(vl_1m, dtype=float)
            np_tl_1m = np.array(tl_1m)
            # float_np_tl_1m = np.array(float_tl_1m, dtype=float)

            # round to 2 decimal places

            # np_ol_1m = np.round(np_ol_1m, 2)
            np_hl_1m = np.round(np_hl_1m, 2)
            np_ll_1m = np.round(np_ll_1m, 2)
            np_cl_1m = np.round(np_cl_1m, 2)
            # np_vl_1m = np.round(np_vl_1m, 2)

            # no need to round of time np arrays

        # logging.info(f'np_tl_1m    {len(np_tl_1m)}  np_cl_1m    {len(np_cl_1m)}')

        bars_response = {

            # "np_ol_1m": np_ol_1m,
            "np_hl_1m": np_hl_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            "np_ll_1m": np_ll_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            "np_cl_1m": np_cl_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            # "np_vl_1m": np_vl_1m[::-1],               # reverse the list since polygon data is orders in asc order
            "np_tl_1m": np_tl_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            # "float_np_tl_1m": float_np_tl_1m[::-1]    # reverse the list since polygon data is orders in asc order
        }

        logging.debug(f"bars_response : {bars_response}")

        return bars_response
'''


def fetch_bars(data_provider):       # data_provider = config.data_provider

    # 1Min
    np_hl_1m = np.array([])
    np_ll_1m = np.array([])
    np_cl_1m = np.array([])
    # np_vl_1m = np.array([])
    np_tl_1m = np.array([])
    # float_np_tl_1m = np.array([])

    ol_15m = list()
    hl_15m = list()
    ll_15m = list()
    tl_15m = list()

    hl_prev_1d = None        # float
    ll_prev_1d = None
    hl_open_30m = None
    ll_open_30m = None
    market_open_price_15m = None

    limit_1m = config.limit_1m
    limit_15m = config.limit_15m    # used for 30m
    limit_1d = config.limit_1d

    if data_provider == 'alpaca':

        ################################# GET 1 MIN BARS #################################

        bar_interval = "1Min"

        payload_1m = {
            "symbols": ticker,
            "limit": limit_1m
            # "start": ts['log_start_1m'],
            # "end": ts['log_end_time']
        }
        base_uri_1m = f'{config.data_url}/bars/{bar_interval}'
        bars_1m = requests.get(url=base_uri_1m, params=payload_1m, headers=headers).json()

        for i, v1m in enumerate(bars_1m[ticker]):
            # CONVERT UNIX TS TO READABLE TS
            v1m_ts_nyc = datetime.fromtimestamp(v1m['t']).astimezone(nyc)  # Covert Unix TS to NYC NOT UTC!!
            v1m_ts = v1m_ts_nyc.strftime('%Y-%m-%d %H:%M:%S')  # Convert to str with format

            # APPEND TO LIST

            # append 1m bars to list
            # ol_1m.append(v1m['o'])
            ll_1m.append(v1m['l'])
            hl_1m.append(v1m['h'])
            cl_1m.append(v1m['c'])
            # vl_1m.append(v1m['v'])
            tl_1m.append(v1m_ts)
            # float_tl_1m.append(v1m['t'])  # to get float ts for linear regression

            # convert to 1m np array
            # added datatype float to avoid real is not double error during MOM cacl
            # np_ol_1m = np.array(ol_1m, dtype=float)
            np_hl_1m = np.array(hl_1m, dtype=float)
            np_ll_1m = np.array(ll_1m, dtype=float)
            np_cl_1m = np.array(cl_1m, dtype=float)
            # np_vl_1m = np.array(vl_1m, dtype=float)
            np_tl_1m = np.array(tl_1m)
            # float_np_tl_1m = np.array(float_tl_1m, dtype=float)

            # round to 2 decimal places

            # np_ol_1m = np.round(np_ol_1m, 2)
            np_hl_1m = np.round(np_hl_1m, 2)
            np_ll_1m = np.round(np_ll_1m, 2)
            np_cl_1m = np.round(np_cl_1m, 2)
            # np_vl_1m = np.round(np_vl_1m, 2)

            # no need to round of time np arrays

        # logging.info(f'np_tl_1m    {len(np_tl_1m)}  np_cl_1m    {len(np_cl_1m)}')

        # 1 Day

        bar_interval = "1D"

        payload_1d = {
            "symbols": ticker,
            "limit": limit_1d,
            "start": ts['prev_dt_str'],
            "end": ts['prev_dt_str']
        }
        base_uri_1d = f'{config.data_url}/bars/{bar_interval}'
        bars_1d = requests.get(url=base_uri_1d, params=payload_1d, headers=headers).json()

        hl_prev_1d = round(float(bars_1d[ticker][0]["h"]), 2)
        ll_prev_1d = round(float(bars_1d[ticker][0]["l"]), 2)

        # 30 Min high low    # rollup last 30 1 min bars or use 15 min

        # using 15 Min

        bar_interval = "15Min"

        payload_15m = {
            "symbols": ticker,
            "limit": limit_15m,
            # "start": ts['open_ts_str'],     # always points to market open
            # "end": ts['open_ts_30m_str']        # always points to 30 mins after market open
        }
        base_uri_15m = f'{config.data_url}/bars/{bar_interval}'
        bars_15m = requests.get(url=base_uri_15m, params=payload_15m, headers=headers).json()

        for i, v15m in enumerate(bars_15m[ticker]):
            # CONVERT UNIX TS TO READABLE TS
            v15m_ts_nyc = datetime.fromtimestamp(v15m['t']).astimezone(nyc)  # Covert Unix TS to NYC NOT UTC!!
            v15m_ts = v15m_ts_nyc.strftime('%Y-%m-%d %H:%M:%S')  # Convert to str with format

            ol_15m.append(v15m['o'])
            ll_15m.append(v15m['l'])
            hl_15m.append(v15m['h'])
            tl_15m.append(v15m_ts)

            np_ol_15m = np.array(ol_15m, dtype=float)
            np_hl_15m = np.array(hl_15m, dtype=float)
            np_ll_15m = np.array(ll_15m, dtype=float)
            np_tl_15m = np.array(tl_15m)

            # using 15 min interval to get opening price since no action would happen until 30 min

            if np_tl_15m[-1] == ts['open_ts_str']:
                market_open_price_15m = round(np_ol_15m[-1], 2)   # set open price using 15 min candle

            if np_tl_15m[-1] == ts['open_ts_30m_str']:
                # i.e. the time now is 30 min after market open
                # time to rollup
                hl_open_30m = round(float(max(np_hl_15m)),2)
                ll_open_30m = round(float(min(np_ll_15m)),2)

        bars_response = {

            # "np_ol_1m": np_ol_1m,
            "np_hl_1m": np_hl_1m,
            "np_ll_1m": np_ll_1m,
            "np_cl_1m": np_cl_1m,
            # "np_vl_1m": np_vl_1m,
            "np_tl_1m": np_tl_1m,
            # "float_np_tl_1m": float_np_tl_1m

            "hl_prev_1d": hl_prev_1d,
            "ll_prev_1d": ll_prev_1d,

            "hl_open_30m": hl_open_30m,
            "ll_open_30m": ll_open_30m,

            "market_open_price_15m": market_open_price_15m
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
        base_uri_1m = f'{config.data_url}/{bar_interval}/{ticker}'

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
            ll_1m.append(v1m['l'])
            hl_1m.append(v1m['h'])
            cl_1m.append(v1m['c'])
            # vl_1m.append(v1m['v'])
            tl_1m.append(v1m_ts)
            # float_tl_1m.append(v1m['t'])  # to get float ts for linear regression

            # convert to 1m np array
            # added datatype float to avoid real is not double error during MOM cacl
            # np_ol_1m = np.array(ol_1m, dtype=float)
            np_hl_1m = np.array(hl_1m, dtype=float)
            np_ll_1m = np.array(ll_1m, dtype=float)
            np_cl_1m = np.array(cl_1m, dtype=float)
            # np_vl_1m = np.array(vl_1m, dtype=float)
            np_tl_1m = np.array(tl_1m)
            # float_np_tl_1m = np.array(float_tl_1m, dtype=float)

            # round to 2 decimal places

            # np_ol_1m = np.round(np_ol_1m, 2)
            np_hl_1m = np.round(np_hl_1m, 2)
            np_ll_1m = np.round(np_ll_1m, 2)
            np_cl_1m = np.round(np_cl_1m, 2)
            # np_vl_1m = np.round(np_vl_1m, 2)

            # no need to round of time np arrays

        # logging.info(f'np_tl_1m    {len(np_tl_1m)}  np_cl_1m    {len(np_cl_1m)}')
        '''
        bars_response = {

            # "np_ol_1m": np_ol_1m,
            "np_hl_1m": np_hl_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            "np_ll_1m": np_ll_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            "np_cl_1m": np_cl_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            # "np_vl_1m": np_vl_1m[::-1],               # reverse the list since polygon data is orders in asc order
            "np_tl_1m": np_tl_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            # "float_np_tl_1m": float_np_tl_1m[::-1]    # reverse the list since polygon data is orders in asc order
        }
        '''

        bars_response = {

            # "np_ol_1m": np_ol_1m,
            "np_hl_1m": np_hl_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            "np_ll_1m": np_ll_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            "np_cl_1m": np_cl_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            # "np_vl_1m": np_vl_1m[::-1],               # reverse the list since polygon data is orders in asc order
            "np_tl_1m": np_tl_1m[::-1],                 # reverse the list since polygon data is orders in asc order
            # "float_np_tl_1m": float_np_tl_1m[::-1]    # reverse the list since polygon data is orders in asc order
        }

        logging.debug(f"bars_response : {bars_response}")

        return bars_response


def support_resistance(low, high, min_touches=3, percent_bounce=0.05, error_margin=0.1):

    '''
    ref: https://www.candlestick.ninja/2019/02/support-and-resistance.html
    determine support and resistances
    :param low:                     np_ll_1m
    :param high:                    np_hl_1m
    :param min_touches:             min touches to establish support or resistance
    :param percent_error_margin:    margin of error to give some room
    :param percent_bounce:          % price needs to bounce off each level
    :param error_margin:            to reduce resistance and increase support for better signals  in cents
    :return:                        sup and res
    '''

    support = resistance = None        # default

    max_1m = np_hl_1m.max()
    min_1m = np_ll_1m.min()

    movement_range = max_1m - min_1m
    bounce_distance = movement_range * percent_bounce

    # Calculate Resistance

    touches = 0
    bounced = False

    for x in range(0, len(np_hl_1m)):
        if abs(max_1m - np_hl_1m[x]) < movement_range and not bounced:
            touches += 1
            bounced = True
        elif abs(max_1m - np_hl_1m[x]) > bounce_distance:
            bounced = False
    if touches >= min_touches:
        resistance = round(max_1m - error_margin, 2)  # to reduce resistance by error margin, used for price_less_than_resistance

    # Calculate Support

    touches = 0
    bounced = False

    for x in range(0, len(np_ll_1m)):
        if abs(np_ll_1m[x] - min_1m) < movement_range and not bounced:
            touches += 1
            bounced = True
        elif abs(np_ll_1m[x] - min_1m) > bounce_distance:
            bounced = False
    if touches >= min_touches:
        support = round(min_1m + error_margin, 2) # to increase support by error margin

    return support,resistance


# TODO: Add ETAs at each step


if __name__ == '__main__':

    day_trade_minimum = config.day_trade_minimum

    buy_order_placed = dict()  # INITIALIZATION
    buy_order_details = dict()

    sell_order_placed = dict()
    sell_order_details = dict()

    secs_to_sleep = config.secs_to_sleep

    order_uri = config.order_uri

    buy_price = 0.000  # float
    sell_price = 0.000  # float

    BUY_PRICE = np.array([0.000])  # initialize here, set to actual avg price at which asset was bought
    sell_target_based_on_profit_percentage = np.array([0])  # initialization

    parser = argparse.ArgumentParser(description="apca - auto trader")

    parser.add_argument('-s', action="store", dest='set',
                        help="symbol set from config, values include 1...5")   # symbol

    arg_val = parser.parse_args()

    set = str(arg_val.set)

    tickers = config.tickers[f"{set}"]

    # tickers = config.ticker            # get ticker dict from config
    num_tickers = len(tickers)

    position_qty = 0    # default
    equity = 0.00       # default to 0
    equity_limit = 0.0  # default
    cash = 0.0          # default cash

    max_open_positions_allowed = int(config.max_open_positions_allowed)

    # logging.info(f"[START][{ticker}]")

    health_check_alert_counter = 0
    x = 0

    while True:  # infinite

        # SET LOGGING LEVEL

        log_file_date = datetime.now().strftime("%Y%m%d")
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', filename=f"logs/set_{set}_{log_file_date}.log")

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

            start_time = datetime.now()                         # to calculate ETA for all tickers

            for ticker in tickers:

                account = dict()                        # default for account response
                buy_price = sell_price = None           # default to 0 for each ticker

                position = False                        # default position to False
                positions_response = dict()             # reset to null dict for each ticker
                position_qty = 0  # default             # reset to default
                position_side = None                    # default position side (buy or sell)
                unrealized_intraday_pl = None              # default intraday pnl in a given open position

                equity = 0.00  # default to 0           # reset to default
                equity_limit = 0.0  # default           # reset to default
                cash = 0.0  # default cash              # reset to default

                # ol_1m = list()                        # reset to null for each ticker
                hl_1m = list()
                ll_1m = list()
                cl_1m = list()
                # vl_1m = list()
                tl_1m = list()
                # float_tl_1m = list()

                hl_15m = list()
                ll_15m = list()
                tl_15m = list()

                logging.info('--' * 40)
                logging.info(f'[{ticker}] [{x}] market_is_open: {market_is_open} time_left:  {trading_time_left} mins')

                if config.live_trade:
                    logging.info(f'[{ticker}] !!! LIVE TRADE !!!')
                else:
                    logging.info(f'[{ticker}] ### PAPER TRADE ###')

                data_provider = config.data_provider
                logging.info(f"[{ticker}] data provider:    {data_provider}")

                # ready to trade
                # TODO: Post Market Open and Close to SLACK

                ############ 0. Setup ############

                ############# GET ACCOUNT INFO

                account_uri = config.account_uri

                account = requests.get(url=account_uri, headers=headers).json()

                equity = float(account["equity"])       # equity
                cash = float(account["cash"])           # cash

                # shorting enabled with override
                account_shorting_enabled = account["shorting_enabled"]  # Only short if enabled, else go long only!!
                bool_shorting_enabled = account_shorting_enabled and config.allow_shorting  # Only short if enabled, else go long only!!

                logging.info(f'[{ticker}] bool_shorting_enabled = {bool_shorting_enabled}   config.allow_shorting: {config.allow_shorting}')

                current_open_positions = 0

                try:
                    pos = requests.get(url=config.positions_uri, headers=headers).json()
                    current_open_positions = len(pos)
                except Exception as e:
                    logging.error(f'[{ticker}] Error fetching current open positions : {str(e)}')


                ############# GET POSITION INFO

                ############  >_< CHECK IF A POSITION EXISTS FROM THE PREVIOUS TRADE ############

                ticker_positions_uri = f'{config.positions_uri}/{ticker}'

                positions_response = None
                try:
                    positions_response = requests.get(url=ticker_positions_uri, headers=headers).json()
                except Exception as e:
                    logging.error(f'[{ticker}] Error fetching position details : {str(e)}')

                # check if key exists in dict, code indicates error or no position
                # TODO: Work on an alternate implementation for checking position

                if "code" not in positions_response:
                    position = True
                    position_qty = abs(int(positions_response['qty']))              # to make -ve units positive
                    position_side = positions_response['side']  # long or short-0.0142711518858308-0.0142711518858308-0.0142711518858308
                    unrealized_intraday_pl = float(positions_response["unrealized_intraday_pl"])  # dropping the decimals

                    if position_side == 'long':
                        buy_price = round(float(positions_response['avg_entry_price']),2)
                        # sell_price = 0.0

                    if position_side == 'short':
                        # buy_price = 0.0
                        sell_price = round(float(positions_response['avg_entry_price']), 2)

                # LIMIT TOTAL TRADABLE AMOUNT

                equity_less_daytrademin = equity - day_trade_minimum  # Total cash in account

                # LIMIT BUYING OR SELLING POWER FOR EACH ALGO. ALGO: STOCK is 1:1

                # cash_limit = cash * config.position_size    # E.G 1 (100%) if trading one stock only

                equity_limit = equity_less_daytrademin / max_open_positions_allowed

                if current_open_positions >= max_open_positions_allowed:
                    cash = 0

                if cash <= 0 and not position:          # else it exits even for stocks with open positions
                    equity_limit = 0                    # added cash check to avoid margin trading
                    logging.info(f'[{ticker}] equity:   ${equity}   cash:   ${cash}     NO CASH AVAILABLE, EXITING')
                    logging.info('--' * 40)
                    # time.sleep(secs_to_sleep)
                    continue

                logging.info(f'[{ticker}] equity:   ${equity}   cash:   ${cash}')
                logging.info(f'[{ticker}] current_open_positions: {current_open_positions}     max_open_positions_allowed: {max_open_positions_allowed}')
                logging.info(f'[{ticker}] equity_limit: [${int(equity_limit)}] of [${int(equity_less_daytrademin)}] day_trade_minimum: [${day_trade_minimum}]')

                logging.info(f'[{ticker}] current_position: [{position_qty}]    side:   [{position_side}]')
                logging.info(f'[{ticker}] buy_price:    ${buy_price}')
                logging.info(f'[{ticker}] sell_price:   ${sell_price}')
                # logging.info(f'[{ticker}] unrealized_intraday_pl:   ${unrealized_intraday_pl}')

                ############# GET OPEN ORDERS

                open_order_exists = False
                open_order_id = None
                open_order_symbol = None
                open_order_qty = None
                open_order_filled_qty = None

                # list all open orders

                null = None  # assign null to None to avoid the NameError: name 'null' is not defined in response
                open_orders = requests.get(url=order_uri, headers=headers).json()

                # https://stackoverflow.com/questions/8653516/python-list-of-dictionaries-search
                order = next((order for order in open_orders if order["symbol"] == ticker), None)

                if order:
                    open_order_exists = True
                    open_order_id = order["id"]
                    open_order_symbol = order["symbol"]
                    open_order_qty = order["qty"]
                    open_order_filled_qty = order["filled_qty"]

                logging.info(
                    f'[{ticker}] open_order_exists: [{open_order_exists}]    open_order_qty:   [{open_order_qty}]')

                ############ >_< FETCH TICKERS BASED ON CURRENT TS ############

                # logging.info(f'[{ticker}] BAR INTERVAL:    {bar_interval} Min')

                bars = fetch_bars(config.data_provider)  # for 1Min

                ############### 1 MIN ###############
                # np_ol_1m = bars['np_ol_1m']
                np_hl_1m = bars['np_hl_1m']
                np_ll_1m = bars['np_ll_1m']
                np_cl_1m = bars['np_cl_1m']
                # np_vl_1m = bars['np_vl_1m']
                np_tl_1m = bars['np_tl_1m']
                # float_np_tl_1m = bars['float_np_tl_1m']

                ############### 15 MIN ###############

                market_open_price_15m = bars["market_open_price_15m"]

                ############### 30 MIN ###############

                hl_open_30m = bars["hl_open_30m"]
                ll_open_30m = bars["ll_open_30m"]

                ############### 1 D ###############

                hl_prev_1d = bars["hl_prev_1d"]
                ll_prev_1d = bars["ll_prev_1d"]

                # logging.debug(f'[{ticker}] NP_OL_1M:    {np_ol_1m}')
                logging.debug(f'[{ticker}] np_hl_1m:    {np_hl_1m}')
                logging.debug(f'[{ticker}] np_ll_1m:    {np_ll_1m}')
                logging.debug(f'[{ticker}] np_cl_1m:    {np_cl_1m}')
                # logging.debug(f'[{ticker}] np_vl_1m:    {np_vl_1m}')
                # logging.debug(f'[{ticker}] np_tl_1m:    {np_tl_1m}')      # TOO MUCH INFO FOR DEBUG

                logging.info(f'[{ticker}] market_open_price_15m:    {market_open_price_15m}')
                logging.info(f'[{ticker}] hl_open_30m:    {hl_open_30m}    ll_open_30m: {ll_open_30m}')
                logging.info(f'[{ticker}] hl_prev_1d:    {hl_prev_1d}  ll_prev_1d:  {ll_prev_1d}')


                ############# INDICATORS / CALCULATIONS ###########################

                # TODO: Cancel order if not executed in 5 min (optional)

                trade_left_open = False  # to check if a trade was left open, initial False

                units_to_buy = units_to_short = int(equity_limit / np_cl_1m[-1])  # assign same value to both

                if (position_qty > 0) or open_order_exists:
                    units_to_buy = units_to_short = 0
                    position = True                     # added since orders were being placed with 0 units and failing

                logging.info(f'[{ticker}] units_to_buy:     {units_to_buy}')
                logging.info(f'[{ticker}] units_to_sell:    {units_to_short}')

                # TODO: [IMPORTANT] derive units to trade dynamically based on cash balance and position size
                # TODO: handle partial fills (optional)


                # Profit percentage (price above buy price) 25% as 0.25, 10% as 0.1
                # used to set -> sell_target_based_on_profit_percentage

                profit_percentage = float(config.profit_percentage)  # 0.2 for 20%
                price_delta = float(config.price_delta)
                sell_target_based_on_profit_percentage = buy_target_based_on_profit_percentage = None

                if buy_price:   # i.e buy_price is not None
                    sell_target_based_on_profit_percentage = buy_price + (
                            buy_price * profit_percentage) + price_delta    # LONG, buy higher than buy price]

                    buy_target_based_on_profit_percentage = sell_price - (
                            sell_price * profit_percentage) - price_delta   # [shorting, buy even lower than sell price]

                # ---> Calculated again below for LONG BUY and SHORT SELL

                logging.info(f"[{ticker}] profit_percentage:                        {profit_percentage}  price_delta:    {price_delta}")
                logging.info(f"[{ticker}] sell_target_based_on_profit_percentage:   {sell_target_based_on_profit_percentage}")
                logging.info(f"[{ticker}] buy_target_based_on_profit_percentage:    {buy_target_based_on_profit_percentage}") # [shorting]

                ########################### BUY / SELL INDICATORS ####################

                bool_closing_time = ts['market_about_to_close']

                logging.info(f"[{ticker}] bool_closing_time:                        {bool_closing_time}")

                ########################### BUY INDICATORS ###########################

                # if market open price is above prev day high
                    # if current price > high of 30 min opening candle
                    # buy with a profit target of 0.3 %

                bool_buy_30min_strategy = False

                if market_open_price_15m and (market_open_price_15m > hl_prev_1d):    # to handle None for market_open_price_15m
                    if np_cl_1m[-1] > hl_open_30m:
                        bool_buy_30min_strategy = True

                logging.info(f"[{ticker}] [{np_cl_1m[-1]}] bool_buy_30min_strategy:    {bool_buy_30min_strategy}")

                bool_buy_profit_target = buy_target_based_on_profit_percentage and (float(np_cl_1m[-1]) <= float(buy_target_based_on_profit_percentage))

                # [SHORT] For sell to buy --> current price [-1] is < or equal to the target price with profit percentage
                logging.debug(f"bool_buy_profit_target [{bool_buy_profit_target}] = float({np_cl_1m[-1]}) <= float({buy_target_based_on_profit_percentage})")


                ################################ SELL AND SHORT INDICATORS #####################

                # if market open price is BELOW prev day LOW
                # if current price < low of 30 min opening candle
                # sell with a profit target of 0.3 %

                bool_short_30min_strategy = False

                if market_open_price_15m and (market_open_price_15m < ll_prev_1d):
                    if np_cl_1m[-1] < ll_open_30m:
                        bool_short_30min_strategy = True

                logging.info(f"[{ticker}] [{np_cl_1m[-1]}] bool_short_30min_strategy:    {bool_short_30min_strategy}")


                bool_sell_price_above_buy = buy_price and (float(np_cl_1m[-1]) > (buy_price + config.small_price_increment))
                # flag to indicate current price is gt buy price

                bool_buy_price_below_sell = sell_price and (float(np_cl_1m[-1]) < (sell_price - config.small_price_increment))
                # flag to indicate current price is less than sell price

                bool_sell_profit_target = sell_target_based_on_profit_percentage and (float(np_cl_1m[-1]) >= float(sell_target_based_on_profit_percentage))
                # current price > sell target

                logging.info(f"[{ticker}] [{np_cl_1m[-1]}] bool_sell_price_above_buy:       {bool_sell_price_above_buy} [{np_cl_1m[-1]} > ({buy_price} + {config.small_price_increment})]")
                logging.info(f"[{ticker}] [{np_cl_1m[-1]}] bool_buy_price_below_sell:       {bool_buy_price_below_sell} [{np_cl_1m[-1]} < ({sell_price} - {config.small_price_increment})]")

                logging.info(f"[{ticker}] [{np_cl_1m[-1]}] bool_buy_profit_target:          {bool_buy_profit_target} [{buy_target_based_on_profit_percentage}]")  # [shorting]
                logging.info(f"[{ticker}] [{np_cl_1m[-1]}] bool_sell_profit_target:         {bool_sell_profit_target} [{sell_target_based_on_profit_percentage}]")

                # logging.info(f"[{ticker}] bool_short_momentum:                              {bool_short_momentum}")

                # TODO: [IMPORTANT] don't use int, it drops the decimal places during comparison, use float instead


                ###########################################
                #####        LONG POSITIONS        ########
                ###########################################


                ################################ LONG BUY SIGNAL - TO OPEN NEW LONG POSITION ##########################

                LONG_BUY_SIGNAL = bool_buy_30min_strategy

                # LONG_BUY_SIGNAL = True

                logging.info(f'[{ticker}] [{np_cl_1m[-1]}] long_buy_signal:              {LONG_BUY_SIGNAL}')



                # TODO: Vol check, add later

                ################################ LONG SELL SIGNAL - TO CLOSE OPEN LONG POSITION ###################

                bool_long_sell_signal = bool_sell_profit_target or (bool_sell_price_above_buy and bool_closing_time)

                LONG_SELL_SIGNAL = bool_long_sell_signal

                # LONG_SELL_SIGNAL = True

                # SELL only if a buy position exists.
                logging.info(f'[{ticker}] [{np_cl_1m[-1]}] long_sell_signal:             {LONG_SELL_SIGNAL} [{np_tl_1m[-1]}]')
                logging.info(f'[{ticker}] [{np_cl_1m[-1]}] unrealized_intraday_pl:       {unrealized_intraday_pl}')

                ###########################################
                #####        SHORT POSITIONS       #######
                ###########################################


                ################################ SHORT SELL SIGNAL - TOP OPEN NEW SHORT POSITION ###########################

                SHORT_SELL_SIGNAL = bool_short_30min_strategy

                # SHORT_SELL_SIGNAL = True

                logging.info(f'[{ticker}] [{np_cl_1m[-1]}] short_sell_signal:            {SHORT_SELL_SIGNAL}')

                ################################ SHORT BUY SIGNAL - TO CLOSE OPEN SHORT POSITION #####################

                bool_short_buy_signal = bool_buy_profit_target or (bool_buy_price_below_sell and bool_closing_time)

                # NOTE: for short resistance and support flip, so bool_price_at_resistance is used
                # in place of bool_price_at_support for short buy
                # Ref: https://www.fxacademy.com/learn/support-and-resistance-basics/sr-basics-long-and-short-trades

                SHORT_BUY_SIGNAL = bool_short_buy_signal

                # SHORT_BUY_SIGNAL = True

                logging.info(f'[{ticker}] [{np_cl_1m[-1]}] short_buy_signal:             {SHORT_BUY_SIGNAL}')

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
    
                if not position and SHORT_SELL_SIGNAL:
                    # short sell
                    pass
                if position and position_side == 'sell' and SHORT_BUY_SIGNAL:
                    # short buy
                    pass
                    
                '''

                ################################ LONG BUY - Open New Long Positionm ######################################

                if LONG_BUY_SIGNAL and not position and not open_order_exists:  # if no position exists and a buy sig is found

                    # TODO: check clock and don't buy 30 min before market close

                    # BUY_PRICE[0] = float((np_cl_1m[-1] + np_cl_1m[-2]) / 2)  # for limit price only
                    # buy_price = round(BUY_PRICE[0], 3)  # for limit price only

                    # limit_price = BUY_PRICE[0]

                    # https://docs.alpaca.markets/api-documentation/web-api/orders/

                    buy_order_data = {
                        'symbol': ticker,
                        'qty': units_to_buy,
                        'side': 'buy',
                        'type': 'market',
                        # 'limit_price': limit_price,
                        'time_in_force': 'day'
                        # 'client_order_id': uuid.uuid4().hex    # generate order_id e.g. '9fe2c4e93f654fdbb24c02b15259716c'
                    }
                    buy_order_data = json.dumps(buy_order_data)

                    logging.info(f'[{ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [long_buy_signal] buy_order_data: {buy_order_data}')

                    buy_order_sent = False
                    buy_order_placed = None
                    try:
                        buy_order_placed = requests.post(url=order_uri, headers=headers,
                                                         data=buy_order_data).json()
                        buy_order_sent = True
                        order_id = buy_order_placed['id']

                        order_text = f"[{ticker}] [{np_cl_1m[-1]} [ORDER] [long_buy_signal] [buy_order_id] {order_id}"
                        logging.info(order_text)
                        # slackit(channel=config.slack_channel, msg=order_text)

                    except Exception as e:
                        error_text = f"[ERROR] [{ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [long_buy_signal] Error placing order: {str(buy_order_placed['message'])}"
                        logging.info(error_text)
                        slackit(channel="ERROR", msg=error_text)

                    '''

                    buy_order_executed = False

                    if buy_order_placed['status'] is not None:  # to check if order was placed
                        order_wait_counter = 0
                        while order_wait_counter <= int(config.order_wait_counter) and not buy_order_executed:  # wait 10 tries

                            # keep checking until order is filled
                            # buy_order_details_data = {'order_id': order_id}
                            # buy_order_details_data = json.dumps(buy_order_details_data)

                            get_order_details_uri = f'{config.base_url}/orders/{order_id}'

                            buy_order_details = requests.get(url=get_order_details_uri, headers=headers).json()

                            logging.info(f"[{ticker}] [LONG_BUY_SIGNAL] [BUY] [WAITING_TO_EXECUTE] [{buy_order_details['submitted_at']}] "
                                  f"[{buy_order_details['status']}] {buy_order_details['side']} "
                                  f"order for {buy_order_details['qty']} shares of {buy_order_details['symbol']}")

                            if buy_order_details['status'] == 'filled':  # or order_details.status == 'partially_filled':
                                buy_order_executed = True

                            logging.info(f"[{ticker}] [long_buy_signal] buy_order_status:    {buy_order_placed['status']} ")

                            order_wait_counter += 1
                            # time.sleep(1)  # WAIT 10 SECS BEFORE NEXT CHECK
                        
                        ###############
                        buy_price = float(buy_order_details['filled_avg_price'])  # ACTUAL FROM BUY ORDER
                        ###############

                        sell_target_based_on_profit_percentage = buy_price + (
                                buy_price * profit_percentage) + price_delta  # LONG, buy higher than buy price]

                        filled_at = buy_order_details['filled_at']
                        filled_qty = buy_order_details['filled_qty']

                        buy_order_text = f"[{ticker}] [LONG_BUY_SIGNAL] {filled_at} {str(buy_order_details['side']).upper()} ORDER OF {filled_qty} [{ticker}] EXECUTED @ {buy_price}" \
                            f" TARGET ${sell_target_based_on_profit_percentage}"

                        logging.info(buy_order_text)

                        # slackit(channel='apca_paper', msg=buy_order_text)  # post to slack

                        logging.debug(f'[{ticker}] [{np_cl_1m[-1]}] [{buy_price}] [{filled_at}]     '
                              f'[long_buy_signal]       {LONG_BUY_SIGNAL}            '
                              f'bool_buy_momentum    {bool_buy_momentum}          '
                              f'position    {position}[{position_qty}]             '
                              f'bool_closing_time     {bool_closing_time}          '
                              f'sell_target_based_on_profit_percentage [{sell_target_based_on_profit_percentage}]        ')

                        position = True # set position to True once BUY is executed
                        
                    else:
                        logging.error(f"[{current_ts}] [ERROR] {buy_order_details['side']} ORDER WAS NOT PLACED")
                        
                    '''

                ################################ LONG_SELL - Close Existing Open Long Position ###########################

                if LONG_SELL_SIGNAL and position and position_side == 'long' and not open_order_exists:

                    # sell_price = round(np_cl_1m[-2], 3)  # set sell price to 1 to 2 bars prior val
                    # for limit price, set sell_price

                    # https://docs.alpaca.markets/api-documentation/web-api/orders/

                    sell_order_data = {
                        'symbol': ticker,
                        'qty': position_qty,    # sell entire position
                        'side': 'sell',
                        'type': 'market',
                        # 'limit_price': limit_price,
                        'time_in_force': 'day'
                        # 'client_order_id': uuid.uuid4().hex    # generate order_id e.g. '9fe2c4e93f654fdbb24c02b15259716c'
                    }
                    sell_order_data = json.dumps(sell_order_data)

                    logging.info(f'[{ticker}] [$PL:{unrealized_intraday_pl}] [{np_cl_1m[-1]}] [long_sell_signal] sell_order_data:    {sell_order_data}')

                    sell_order_sent = False
                    sell_order_placed = None
                    try:
                        sell_order_placed = requests.post(url=order_uri, headers=headers,
                                                          data=sell_order_data).json()
                        sell_order_sent = True
                        order_id = sell_order_placed['id']

                        order_text = f"[{ticker}] [$PL:{unrealized_intraday_pl}] [{np_cl_1m[-1]}] [ORDER] [long_sell_signal] [sell_order_id] [{order_id}]"
                        logging.info(order_text)
                        slackit(channel=config.slack_channel, msg=order_text)

                    except Exception as e:
                        error_text = f"[ERROR] [{ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [long_sell_signal] Error placing order: {str(sell_order_placed['message'])}"
                        logging.info(error_text)
                        slackit(channel="ERROR", msg=error_text)

                    '''
                    sell_order_executed = False

                    # logging.info(f"SELL Order Placed Status Code:           {sell_order_placed['status_code']} ")

                    if sell_order_placed['status'] is not None:

                        order_wait_counter = 0
                        while order_wait_counter <= int(config.order_wait_counter) and not sell_order_executed:

                            # keep checking until order is filled

                            get_order_details_uri = f'{config.base_url}/orders/{order_id}'

                            sell_order_details = requests.get(url=get_order_details_uri, headers=headers).json()

                            waiting_to_sell = f"[{ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [LONG_SELL_SIGNAL] [SELL] [WAITING_TO_EXECUTE] [{sell_order_details['submitted_at']}] " \
                                f"[{sell_order_details['status']}] {sell_order_details['side']} " \
                                f"order for {sell_order_details['qty']} shares of {sell_order_details['symbol']}"

                            logging.info(waiting_to_sell)

                            # slackit(channel='apca-paper', msg=waiting_to_sell)

                            if sell_order_details['status'] == 'filled':  # or order_details.status == 'partially_filled':
                                sell_order_executed = True

                            logging.info(f"[{ticker}] [LONG_SELL_SIGNAL] SELL ORDER STATUS:   {sell_order_placed['status']} ")

                            order_wait_counter += 1

                            # time.sleep(1)  # WAIT 10 SECS BEFORE NEXT CHECK

                        ###############
                        sell_price = round(float(sell_order_details['filled_avg_price']), 2)
                        ###############

                        filled_at = sell_order_details['filled_at']

                        side = str(sell_order_details['side']).upper()

                        profit = round((float(sell_price - buy_price) * position_qty), 2)

                        sell_order_text = f'[{ticker}] [LONG_SELL_SIGNAL] [{filled_at}] [EXECUTED] {side} ORDER WAS EXECUTED @ {sell_price}'

                        logging.info(sell_order_text)

                        # slackit(channel='apca_paper', msg=sell_order_text)  # post to slack

                        trade_text = f'[{ticker}] [LONG] [{current_ts}] BUY {position_qty} @ ${buy_price} SELL @ ${sell_price}  PNL ${profit}'

                        logging.info(trade_text)
                        slackit(channel=config.slack_channel, msg=trade_text)    # post to slack

                    # signals.append(signal)

                    logging.debug(f'[{ticker}] [{np_tl_1m[-1]}] [{sell_price}]     '
                          f'[long_sell_signal]      {LONG_SELL_SIGNAL}            '
                          f'MOMENbool_sell_momentumTUM    {bool_sell_momentum}         '
                          f'position    {position}              '
                          f'bool_closing_time     {bool_closing_time}          '
                          f'sell_target_based_on_profit_percentage [{sell_target_based_on_profit_percentage}] {bool_sell_profit_target}  '
                          f'bool_sell_price_above_buy       {bool_sell_price_above_buy}')

                    position = False  # set position to false once a sale has completed
                    
                    '''

                ################################ SHORT SELL - Open New Short Position #####################################

                if not position and SHORT_SELL_SIGNAL:

                    # sell_price = round(np_cl_1m[-2], 3)  # set sell price to 1 to 2 bars prior val
                    # for limit price, set sell_price

                    # https://docs.alpaca.markets/api-documentation/web-api/orders/

                    sell_order_data = {
                        'symbol': ticker,
                        'qty': units_to_short,    # units to short
                        'side': 'sell',
                        'type': 'market',
                        # 'limit_price': limit_price,
                        'time_in_force': 'day'
                        # 'client_order_id': uuid.uuid4().hex    # generate order_id e.g. '9fe2c4e93f654fdbb24c02b15259716c'
                    }
                    sell_order_data = json.dumps(sell_order_data)

                    logging.info(f'[{ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [short_sell_signal] sell_order_data:    {sell_order_data}')

                    sell_order_sent = False
                    sell_order_placed = None
                    try:
                        sell_order_placed = requests.post(url=order_uri, headers=headers,
                                                          data=sell_order_data).json()
                        sell_order_sent = True
                        order_id = sell_order_placed['id']

                        order_text = f"[{ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [ORDER] [short_sell_signal] [sell_order_id] [{order_id}]"
                        logging.info(order_text)
                        # slackit(channel=config.slack_channel, msg=order_text)

                    except Exception as e:
                        error_text = f"[ERROR] [{ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [short_sell_signal] Error placing order: {str(sell_order_placed['message'])})"
                        logging.info(error_text)
                        slackit(channel="ERROR", msg=error_text)

                    '''
                    sell_order_executed = False

                    # logging.info(f"SELL Order Placed Status Code:           {sell_order_placed['status_code']} ")

                    if sell_order_placed['status'] is not None:
                        order_wait_counter = 0
                        while order_wait_counter <= int(config.order_wait_counter) and not sell_order_executed:

                            # keep checking until order is filled

                            get_order_details_uri = f'{config.base_url}/orders/{order_id}'

                            sell_order_details = requests.get(url=get_order_details_uri, headers=headers).json()

                            waiting_to_sell = f"[{ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [{order_wait_counter}] [SHORT_SELL_SIGNAL] [SELL] [WAITING_TO_EXECUTE] [{sell_order_details['submitted_at']}] " \
                                f"[{sell_order_details['status']}] {sell_order_details['side']} " \
                                f"order for {sell_order_details['qty']} shares of {sell_order_details['symbol']}"

                            logging.info(waiting_to_sell)

                            # slackit(channel='apca-paper', msg=waiting_to_sell)

                            if sell_order_details['status'] == 'filled':  # or order_details.status == 'partially_filled':
                                sell_order_executed = True

                            logging.info(f"[{ticker}] [{order_wait_counter}] [SHORT_SELL_SIGNAL] SELL ORDER STATUS:   {sell_order_placed['status']} ")

                            order_wait_counter += 1
                            # time.sleep(1)  # WAIT 1 SEC BEFORE NEXT CHECK

                        ###############
                        sell_price = round(float(sell_order_details['filled_avg_price']), 2)
                        ###############

                        buy_target_based_on_profit_percentage = sell_price - (
                                sell_price * profit_percentage) - price_delta # [shorting, buy even lower than sell price]

                        filled_at = sell_order_details['filled_at']

                        side = str(sell_order_details['side']).upper()

                        sell_order_text = f'[{ticker}] [SHORT_SELL_SIGNAL] [{filled_at}] [EXECUTED] {side} ORDER WAS EXECUTED @ {sell_price}'

                        logging.info(sell_order_text)

                        # post to slack
                        # --- > commented due to too many alerts
                        # slackit(channel=config.slack_channel, msg=sell_order_text)    # post to slack

                    # signals.append(signal)

                    logging.debug(f'[{ticker}] [{np_tl_1m[-1]}] [{sell_price}]     '
                          f'[SHORT_SELL_SIGNAL]      {SHORT_SELL_SIGNAL}            '
                          f'bool_short_momentum    {bool_short_momentum}         '
                          f'position    {position}[{position_qty}]              '
                          f'bool_closing_time     {bool_closing_time}          '
                          f'buy_target_based_on_profit_percentage [{buy_target_based_on_profit_percentage}] {bool_buy_profit_target}  '
                          f'bool_buy_price_below_sell       {bool_buy_price_below_sell}')

                    position = True  # set position to false once short sell is initiated
                    
                    '''

                ################################ SHORT BUY - Close Existing Short Sell Position ###########################

                if position and position_side == 'short' and SHORT_BUY_SIGNAL:  # if a sell position exists and a short buy sig is found

                    buy_order_data = {
                        'symbol': ticker,
                        'qty': position_qty,
                        'side': 'buy',
                        'type': 'market',
                        # 'limit_price': limit_price,
                        'time_in_force': 'day'
                        # 'client_order_id': uuid.uuid4().hex    # generate order_id e.g. '9fe2c4e93f654fdbb24c02b15259716c'
                    }
                    buy_order_data = json.dumps(buy_order_data)

                    logging.debug(f'[{ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [short_buy_signal] buy_order_data: {buy_order_data}')

                    buy_order_sent = False
                    buy_order_placed = None
                    try:
                        buy_order_placed = requests.post(url=order_uri, headers=headers,
                                                         data=buy_order_data).json()
                        buy_order_sent = True
                        order_id = buy_order_placed['id']

                        order_text = f"[{ticker}] [$PL:{unrealized_intraday_pl}] [{np_cl_1m[-1]}] [ORDER]  [short_buy_signal] [buy_order_id] {order_id}"

                        logging.info(order_text)
                        slackit(channel=config.slack_channel, msg=order_text)

                    except Exception as e:
                        error_text = f"[ERROR] [{ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [short_buy_signal] Error placing order: {str(buy_order_placed['message'])}"
                        logging.info(error_text)
                        slackit(channel="ERROR", msg=error_text)
                    '''
                    buy_order_executed = False

                    if buy_order_placed['status'] is not None:  # to check if order was placed
                        order_wait_counter = 0
                        while order_wait_counter <= int(config.order_wait_counter) and not buy_order_executed:

                            # keep checking until order is filled
                            # buy_order_details_data = {'order_id': order_id}
                            # buy_order_details_data = json.dumps(buy_order_details_data)

                            get_order_details_uri = f'{config.base_url}/orders/{order_id}'

                            buy_order_details = requests.get(url=get_order_details_uri, headers=headers).json()

                            logging.info(f"[{ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}] [{order_wait_counter}] [SHORT_BUY_SIGNAL] [BUY] [WAITING_TO_EXECUTE] [{buy_order_details['submitted_at']}] "
                                  f"[{buy_order_details['status']}] {buy_order_details['side']} "
                                  f"order for {buy_order_details['qty']} shares of {buy_order_details['symbol']}")

                            if buy_order_details['status'] == 'filled':  # or order_details.status == 'partially_filled':
                                buy_order_executed = True

                            logging.info(f"[{ticker}] [{order_wait_counter}] [SHORT_BUY_SIGNAL] BUY_ORDER_STATUS:    {buy_order_placed['status']} ")

                            # time.sleep(1)  # WAIT 5 SECS BEFORE NEXT CHECK

                        ###############
                        buy_price = float(buy_order_details['filled_avg_price'])  # ACTUAL FROM BUY ORDER
                        ###############

                        filled_at = buy_order_details['filled_at']
                        filled_qty = buy_order_details['filled_qty']

                        # # TODO: [IMPORTANT] Use actual fill price to derive sell_target_based_on_profit_percentage

                        buy_order_text = f"[{ticker}] [{np_tl_1m[-1]}] [{np_cl_1m[-1]}]  [SHORT_BUY_SIGNAL] [{filled_at}] {str(buy_order_details['side']).upper()} ORDER OF {filled_qty} [{ticker}] EXECUTED @ {buy_price}"

                        logging.debug(buy_order_text)

                        profit = round((float(sell_price - buy_price) * position_qty), 2)   # shorting profit reversed

                        trade_text = f'[{ticker}] [SHORT] [{current_ts}] SELL {position_qty} @ ${sell_price} BUY @ ${buy_price} \n PNL ${profit}'

                        logging.info(trade_text)
                        slackit(channel=config.slack_channel, msg=trade_text)    # post to slack

                        # post to slack

                        logging.debug(f'[{ticker}] [SHORT_BUY_SIGNAL] [{np_cl_1m[-1]}] [{buy_price}] [{filled_at}]     '
                              f'[SHORT_BUY_SIGNAL]       {SHORT_BUY_SIGNAL}            '
                              f'bool_close_short_momentum    {bool_close_short_momentum}          '
                              f'position    {position}[{position_qty}]             '
                              f'bool_closing_time     {bool_closing_time}          '
                              f'buy_target_based_on_profit_percentage [{buy_target_based_on_profit_percentage}]        ')

                        position = False # set position to True once BUY is executed
                    else:
                        logging.error(f"[{current_ts}] [SHORT_BUY_SIGNAL] [ERROR] {buy_order_details['side']} ORDER WAS NOT PLACED")
                    '''

                ###########################################################################################################

        # HEALTH CHECK START ------ >>

        end_time = datetime.now() - start_time
        logging.info(f"Finished {num_tickers} tickers in {end_time.seconds} seconds")

        if health_check_alert_counter == 1:
            msg = f'SET {set} [CHECK] OK'
            slackit(channel="CHECK", msg=msg)                    # Post to health-check slack channel
        elif health_check_alert_counter > 120:
            health_check_alert_counter = 0

        health_check_alert_counter += 1

        # HEALTH CHECK END --------- <<

        x += 1

        # logging.info('\n')
        logging.info('--'*40)
        time.sleep(int(secs_to_sleep))


