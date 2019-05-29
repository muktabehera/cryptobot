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

    logging.debug(ts_dict)

    return ts_dict


def fetch_bars():

    # TODO: pull bars async
    # TODO: Convert bar_interval as a method instead of 1Min, 5Min sections

    start_ts = ts['open_ts']            # market open ts
    # logging.info(f'start_ts:                   {start_ts}')
    end_ts = ts['clock_ts']             # current ts
    # logging.info(f'end_ts:                     {end_ts}')
    market_close_ts = ts['close_ts']    # to prevent getting more bars after market has closed for the day
    # logging.info(f'market_close_ts:                    {market_close_ts}')

    paper_limit_1m = config.paper_limit_1m
    paper_limit_5m = config.paper_limit_5m
    paper_limit_15m = config.paper_limit_15m

    ################################# GET 1 MIN BARS #################################

    bar_interval = "1Min"

    payload_1m = {
        "symbols": ticker,
        "limit": paper_limit_1m,
        "start": ts['log_start_1m'],
        "end": ts['log_end_time']
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
        # ll_1m.append(v1m['l'])
        # hl_1m.append(v1m['h'])
        cl_1m.append(v1m['c'])
        vl_1m.append(v1m['v'])
        tl_1m.append(v1m_ts)

        # convert to 1m np array
        # added datatype float to avoid real is not double error during MOM cacl
        # np_ol_1m = np.array(ol_1m, dtype=float)
        # np_hl_1m = np.array(hl_1m, dtype=float)
        # np_ll_1m = np.array(ll_1m, dtype=float)
        np_cl_1m = np.array(cl_1m, dtype=float)
        np_vl_1m = np.array(vl_1m, dtype=float)
        np_tl_1m = np.array(tl_1m)

    # logging.info(f'np_tl_1m    {len(np_tl_1m)}  np_cl_1m    {len(np_cl_1m)}')

    ################################# GET 5 MIN BARS #################################
    '''

    bar_interval = "5Min"

    payload_5m = {
        "symbols": ticker,
        "limit": paper_limit_5m,
        "start": ts['log_start_5m'],
        "end": ts['log_end_time']
    }

    base_uri_5m = f'{config.data_url}/bars/{bar_interval}'
    bars_5m = requests.get(url=base_uri_5m, params=payload_5m, headers=headers).json()

    for i, v5m in enumerate(bars_5m[ticker]):
        # CONVERT UNIX TS TO READABLE TS
        v5m_ts_nyc = datetime.fromtimestamp(v5m['t']).astimezone(nyc)  # Covert Unix TS to NYC NOT UTC!!
        v5m_ts = v5m_ts_nyc.strftime('%Y-%m-%d %H:%M:%S')  # Convert to str with format

        # APPEND TO LIST

        # append 1m bars to list
        ol_5m.append(v5m['o'])
        ll_5m.append(v5m['l'])
        hl_5m.append(v5m['h'])
        cl_5m.append(v5m['c'])
        vl_5m.append(v5m['v'])
        tl_5m.append(v5m_ts)

        # convert to 1m np array
        # added datatype float to avoid real is not double error during MOM cacl
        np_ol_5m = np.array(ol_5m, dtype=float)
        np_hl_5m = np.array(hl_5m, dtype=float)
        np_ll_5m = np.array(ll_5m, dtype=float)
        np_cl_5m = np.array(cl_5m, dtype=float)
        np_vl_5m = np.array(vl_5m, dtype=float)
        np_tl_5m = np.array(tl_5m)
        
        '''
    # logging.info(f'np_tl_1m    {len(np_tl_1m)}  np_cl_1m    {len(np_cl_1m)}')

    bars_response = {

        # "np_ol_1m": np_ol_1m,
        # "np_hl_1m": np_hl_1m,
        # "np_ll_1m": np_ll_1m,
        "np_cl_1m": np_cl_1m,
        "np_vl_1m": np_vl_1m,
        "np_tl_1m": np_tl_1m
    }

    '''
    
    "np_ol_5m": np_ol_5m,
    "np_hl_5m": np_hl_5m,
    "np_ll_5m": np_ll_5m,
    "np_cl_5m": np_cl_5m,
    "np_vl_5m": np_vl_5m,
    "np_tl_5m": np_tl_5m
    
    '''

    logging.debug(f"bars_response : {bars_response}")

    return bars_response

# TODO: Add ETAs at each step


if __name__ == '__main__':

    day_trade_minimum = 25000.00        # TODO: SET day_trade_minimum TO 0 LATER

    buy_order_placed = dict()  # INITIALIZATION
    buy_order_details = dict()

    sell_order_placed = dict()
    sell_order_details = dict()

    # bar_interval = config.bar_interval

    order_uri = config.order_uri
    clock_uri = config.clock_uri

    buy_price = 0.000  # float
    sell_price = 0.000  # float

    BUY_PRICE = np.array([0.000])  # initialize here, set to actual avg price at which asset was bought
    sell_target_based_on_profit_percentage = np.array([0])  # initialization

    parser = argparse.ArgumentParser(description="apca - auto trader")

    parser.add_argument('-s', action="store", dest='symbol',
                        help="ticker symbol from config")   # symbol

    arg_val = parser.parse_args()

    symbol = str(arg_val.symbol)        # passed to the -s switch e.g. -s V or -s MSFT or -s GOOG

    ticker = config.ticker[f"{symbol}"]

    position_qty = 0  # default

    health_check_alert_counter = 0


    # logging.info(f"[START][{ticker}]")

    x = 0

    while True:  # infinite

        # SET LOGGING LEVEL
        log_file_date = datetime.now().strftime("%Y%m%d")
        logger = logging.getLogger(__name__)

        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', filename=f"logs/{ticker}_{log_file_date}.log")

        if config.live_trade:
            logging.info(f'[{ticker}] !!! LIVE TRADE !!!')
        else:
            logging.info(f'[{ticker}] ### PAPER TRADE ###')

        # Reset the lists each run to null
        '''
        tl_5m = list()
        ol_5m = list()
        hl_5m = list()
        ll_5m = list()
        cl_5m = list()
        vl_5m = list()
        '''

        # ol_1m = list()
        # hl_1m = list()
        # ll_1m = list()
        cl_1m = list()
        vl_1m = list()
        tl_1m = list()


        # logging.info(f'Entering x = {x}')

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

        logging.info(f'[{x}] market_is_open: {market_is_open} time_left:  {trading_time_left} mins')

        # new_bar_available = True

        if market_is_open:

            # ready to trade
            # TODO: Post Market Open and Close to SLACK

            ############ 0. Setup ############

            ############# GET ACCOUNT INFO

            account_uri = config.account_uri

            account = requests.get(url=account_uri, headers=headers).json()

            shorting_enabled = account["shorting_enabled"]  # Only short if enabled, else go long only!!

            logging.info(f'[{ticker}] shorting_enabled = {shorting_enabled}')

            # LIMIT TOTAL TRADABLE AMOUNT

            cash = float(account['cash']) - day_trade_minimum  # Total cash in account

            # LIMIT BUYING OR SELLING POWER FOR EACH ALGO. ALGO: STOCK is 1:1

            cash_limit = cash * config.position_size    # E.G 1 (100%) if trading one stock only

            logging.info(f'[{ticker}] cash: [${int(cash_limit)}] of [${int(cash)}] day_trade_minimum: [${day_trade_minimum}]')


            ############# GET POSITION INFO

            ############  >_< CHECK IF A POSITION EXISTS FROM THE PREVIOUS TRADE ############

            positions_uri = f'{config.base_url}/positions/{ticker}'

            positions_response = requests.get(url=positions_uri, headers=headers).json()

            position = False    # default position to False
            position_side = None    # default position side (buy or sell)

            # check if key exists in dict, code indicates error or no position
            # TODO: Work on an alternate implementation for checking position

            if 'code' not in positions_response:
                position = True
                position_qty = int(positions_response['qty']).__abs__()     # to make -ve units positive
                position_side = positions_response['side']  # long or short
                buy_price = round(float(positions_response['avg_entry_price']),2)

            logging.info(f'[{ticker}] current_position: [{position_qty}]')
            logging.info(f'[{ticker}] buy_price:    ${buy_price}')


            ############ >_< FETCH TICKERS BASED ON CURRENT TS ############

            # logging.info(f'[{ticker}] BAR INTERVAL:    {bar_interval} Min')

            bars = fetch_bars()  # for 1Min

            ############### 1 MIN ###############
            # np_ol_1m = bars['np_ol_1m']
            # np_hl_1m = bars['np_hl_1m']
            # np_ll_1m = bars['np_ll_1m']
            np_cl_1m = bars['np_cl_1m']
            np_vl_1m = bars['np_vl_1m']
            np_tl_1m = bars['np_tl_1m']


            # logging.debug(f'[{ticker}] NP_OL_1M:    {np_ol_1m}')
            # logging.debug(f'[{ticker}] NP_HL_1M:    {np_hl_1m}')
            # logging.debug(f'[{ticker}] NP_LL_1M:    {np_ll_1m}')
            logging.debug(f'[{ticker}] np_cl_1m:    {np_cl_1m}')
            logging.debug(f'[{ticker}] np_vl_1m:    {np_vl_1m}')
            # logging.debug(f'[{ticker}] np_tl_1m:    {np_tl_1m}')      # TOO MUCH INFO FOR DEBUG

            ############### 5 MIN ###############

            '''
            
            np_ol_5m = bars['np_ol_5m']
            np_hl_5m = bars['np_hl_5m']
            np_ll_5m = bars['np_ll_5m']
            np_cl_5m = bars['np_cl_5m']
            np_vl_5m = bars['np_vl_5m']
            np_tl_5m = bars['np_tl_5m']
            
            logging.debug(f'[{ticker}] NP_OL_5M:    {np_ol_5m}')
            logging.debug(f'[{ticker}] NP_HL_5M:    {np_hl_5m}')
            logging.debug(f'[{ticker}] NP_LL_5M:    {np_ll_5m}')
            logging.debug(f'[{ticker}] NP_CL_5M:    {np_cl_5m}')
            logging.debug(f'[{ticker}] NP_VL_5M:    {np_vl_5m}')
            logging.debug(f'[{ticker}] NP_TL_5M:    {np_tl_5m}')

            '''


            ############# INDICATORS / CALCULATIONS ###########################

            mom_cl_1m = talib.MOM(np_cl_1m, timeperiod=1)          # 1M CLOSE MOMENTUM
            logging.debug(f'[{ticker}] mom_cl_1m:  {mom_cl_1m}')

            '''            
            mom_vl_1m = talib.MOM(np_vl_1m, timeperiod=1)          # 1M VOL MOMENTUM
            avg_vl5_1m = talib.SMA(np_vl_1m, timeperiod=5)
            bool_buy_confirmation_vol = mom_vl_1m[-1] > 0 and mom_vl_1m[-2] > 0

            # current vol is greater than or equal to avg vol in the last 5 mins
            # bool_buy_vol = True, means vol is good for a buy

            
            logging.info(f'[{ticker}] MOM_VL_1M:  {mom_vl_1m}')

            mom_cl_5m = talib.MOM(np_cl_5m, timeperiod=1)          # 1M CLOSE MOMENTUM
            mom_vl_5m = talib.MOM(np_vl_5m, timeperiod=1)          # 1M VOL MOMENTUM
            logging.info(f'[{ticker}] MOM_CL_5M:  {mom_cl_5m}')
            logging.info(f'[{ticker}] MOM_VL_5M:  {mom_vl_5m}')
            '''

            ################### TREND #################

            # To get 1 M Uptrend, use 5 Min Window
                # calculate sma5_1m, timeperiod 5 (i.e. anything greater than 3)
                # if mom_sma5_1m[-1] > 0 and mom_sma5_1m[-2] > 0 --> UPTREND_5M

            # Reverse for downtrend
                # calculate sma5_1m
                # cal mom_sma5_1m for last 3 values
                # if mom_sma5_1m[-1] < 0 and mom_sma5_1m < 0 --> DOWNTREND_5M

            bool_uptrend_1m = False      # default
            bool_downtrend_1m = False    # default
            bool_sideways_1m = False     # default

            # TODO: Get 15 min and an hour long trend at least

            sma_1m = talib.SMA(np_cl_1m, timeperiod=10) # 10 to keep it smooth

            if (sma_1m[-1] >= sma_1m[-2]) and (sma_1m[-2] >= sma_1m[-3]):   # > or = for uptrend to relax it a little
                bool_uptrend_1m = True
                logging.debug(f"bool_uptrend_1m [{np_cl_1m[-1]}] [{bool_uptrend_1m} = {sma_1m[-1]} > {sma_1m[-2]}) and ({sma_1m[-2]} > {sma_1m[-3]}")

            if (sma_1m[-1] <= sma_1m[-2]) and (sma_1m[-2] <= sma_1m[-3]):
                bool_downtrend_1m = True
                logging.debug(f"bool_downtrend_1m [{np_cl_1m[-1]}]  [{bool_downtrend_1m}] = {sma_1m[-1]} < {sma_1m[-2]}) and ({sma_1m[-2]} < {sma_1m[-3]}")

            # if (sma_1m[-1] == sma_1m[-2]) and (sma_1m[-2] == sma_1m[-3]):
            #     bool_sideways_1m = True

            logging.info(f'[{ticker}] bool_uptrend_1m:  {bool_uptrend_1m}')
            logging.info(f'[{ticker}] bool_downtrend_1m:  {bool_downtrend_1m}')
            # logging.info(f'[{ticker}] bool_sideways_1m:  {bool_sideways_1m}')


            ################### BOLLINGER BANDS FOR DYNAMIC SUPPORT AND RESISTANCE

            '''
            
            bb_cl_upperband_1m, bb_cl_midband_1m, bb_cl_lowerband_1m = talib.BBANDS(np_cl_1m, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

            bb_support_cl_1m = bb_cl_lowerband_1m
            # set lowerband as dynamic support

            bb_resistance_cl_1m = bb_cl_upperband_1m
            # set upper band as dynamic resistance

            bb_mid_cl_1m = bb_cl_midband_1m
            # set mid band as mid band
            
            '''

            ######### BULL FLAG EXCEPTION ##########

            '''
            Added one key filter. I found that at times I could get shaken out of a play that was consolidating 
            (that is, a bull flag) when prices made a series of lower closes within that consolidation. 
            So, if there are three lower closes, but this price action does not go below the signal bar’s low, 
            then I ignore the signal. 
            
            For this indicator on a long signal, then, the trigger bar would be the first bar that has a higher low 
            than the previous bar. The next bar that closes above the high of this trigger bar paints this previous 
            low bar, which now becomes the swing low point.
            '''

            bull_flag_1m = False

            if np_cl_1m[-1] <= np_cl_1m[-3] or np_cl_1m[-1] <= np_cl_1m[-4]:    # check current price is
                bull_flag_1m = True

            bear_flag_1m = False   # [shorting]

            if np_cl_1m[-1] >= np_cl_1m[-3] or np_cl_1m[-1] >= np_cl_1m[-4]:
                bear_flag_1m = True    # [shorting]

            logging.info(f'[{ticker}] bull_flag_1m:  {bull_flag_1m}')
            logging.info(f'[{ticker}] bear_flag_1m:  {bear_flag_1m}') # [shorting]

            ####################################################################

            # TODO: Cancel order if not executed in 5 min (optional)

            trade_left_open = False  # to check if a trade was left open, initial False

            units_to_buy = units_to_short = int(cash_limit / np_cl_1m[-1]) # assign same value to both

            logging.info(f'[{ticker}] units_to_buy:     {units_to_buy}')
            logging.info(f'[{ticker}] units_to_sell:    {units_to_short}')

            # TODO: [IMPORTANT] derive units to trade dynamically based on cash balance and position size
            # TODO: handle partial fills (optional)


            # Profit percentage (price above buy price) 25% as 0.25, 10% as 0.1
            # used to set -> sell_target_based_on_profit_percentage

            profit_percentage = float(config.profit_percentage)  # 0.2 for 20%
            price_delta = float(config.price_delta)

            sell_target_based_on_profit_percentage = buy_price + (
                    buy_price * profit_percentage) + price_delta # LONG, buy higher than buy price]

            buy_target_based_on_profit_percentage = sell_price - (
                    sell_price * profit_percentage) - price_delta  # [shorting, buy even lower than sell price]

            # ---> Calculated again below for LONG BUY and SHORT SELL

            logging.info(f"[{ticker}] profit_percentage:   {profit_percentage}  price_delta:    {price_delta}")
            # logging.info(f"[{ticker}] sell_target_based_on_profit_percentage:   {sell_target_based_on_profit_percentage}")
            # logging.info(f"[{ticker}] buy_target_based_on_profit_percentage:    {buy_target_based_on_profit_percentage}") # [shorting]


            ########################### BUY / SELL INDICATORS ####################

            bool_closing_time = ts['market_about_to_close']

            ########################### BUY INDICATORS ###########################

            bool_buy_momentum = (mom_cl_1m[-1] > 0 and mom_cl_1m[-2] > 0) and (mom_cl_1m[-2] >= mom_cl_1m[-1])
            logging.debug(f"bool_buy_momentum = ({mom_cl_1m[-1]} > 0 and {mom_cl_1m[-2]} > 0) and ({mom_cl_1m[-2]} >= {mom_cl_1m[-1]}) [{bool_buy_momentum}]")

            bool_close_short_momentum = mom_cl_1m[-1] > 0 and mom_cl_1m[-2] > 0
            # similar to buy but without the 2nd condition
            logging.debug(f"bool_close_short_momentum [{bool_close_short_momentum}] = ({mom_cl_1m[-1]} > 0 and {mom_cl_1m[-2]} > 0)")

            # TODO: Look for a large move on a single candle as well. Questioning if that would happen in 1 Min?
            # TODO: To answer, check what the max price has moved in 1 Min. Worth it?

            bool_buy_profit_target = float(np_cl_1m[-1]) <= float(buy_target_based_on_profit_percentage)
            # [SHORT] For sell to buy --> current price [-1] is < or equal to the target price with profit percentage
            logging.debug(f"bool_buy_profit_target [{bool_buy_profit_target}] = float({np_cl_1m[-1]}) <= float({buy_target_based_on_profit_percentage})")

            logging.info(f"[{ticker}] bool_closing_time:  {bool_closing_time}")


            ################################ SELL AND SHORT INDICATORS #####################

            bool_sell_momentum = mom_cl_1m[-1] < 0 and mom_cl_1m[-2] < 0  # current and prev momentum are positive
            # use sell momentum to close a long position

            bool_short_momentum = (mom_cl_1m[-1] < 0 and mom_cl_1m[-2] < 0) and (mom_cl_1m[-1] <= mom_cl_1m[-2])
            # use short momentum to initiate a short position

            # TODO: SHORT MOMENTUM needs some more thought

            bool_sell_price_above_buy = float(np_cl_1m[-1]) > buy_price
            # flag to indicate current price is gt buy price

            bool_buy_price_below_sell = float(np_cl_1m[-1]) < sell_price
            # flag to indicate current price is less than sell price

            bool_sell_profit_target = float(np_cl_1m[-1]) >= float(sell_target_based_on_profit_percentage)
            # current price > sell target

            logging.info(f"[{ticker}] bool_buy_momentum:  {bool_buy_momentum}")
            logging.info(f"[{ticker}] bool_sell_momentum:  {bool_sell_momentum} [{mom_cl_1m[-1]} < 0 AND {mom_cl_1m[-2]} < 0]")

            logging.info(f"[{ticker}] bool_sell_price_above_buy:  {bool_sell_price_above_buy} [{np_cl_1m[-1]} > {buy_price}]")
            logging.info(f"[{ticker}] bool_buy_price_below_sell:  {bool_buy_price_below_sell} [{np_cl_1m[-1]} < {sell_price}]")

            logging.info(f"[{ticker}] bool_buy_profit_target:  {bool_buy_profit_target} [{buy_target_based_on_profit_percentage}]")  # [shorting]
            logging.info(f"[{ticker}] bool_sell_profit_target:  {bool_sell_profit_target} [{sell_target_based_on_profit_percentage}]")

            logging.info(f"[{ticker}] bool_short_momentum:  {bool_short_momentum}")

            # TODO: [IMPORTANT] don't use int, it drops the decimal places during comparison, use float instead



            ###########################################
            #####        LONG POSITIONS        ########
            ###########################################


            ################################ BUY SIGNAL ###########################

            LONG_BUY_SIGNAL = bool_buy_momentum and \
                              bool_uptrend_1m and \
                              not bool_closing_time

            logging.info(f'[{ticker}] long_buy_signal:  {LONG_BUY_SIGNAL} [{np_tl_1m[-1]}] [{np_cl_1m[-1]}]')

            # TODO: add resistance check during buy
            # TODO: Vol check, add later

            ################################ SELL SIGNAL ###########################

            LONG_SELL_SIGNAL = bool_sell_profit_target or \
                               (bool_sell_momentum and bool_sell_price_above_buy and not bull_flag_1m) or \
                               (bool_sell_price_above_buy and bool_closing_time)

            # SELL only if a buy position exists.

            logging.info(f'[{ticker}] long_sell_signal:   {LONG_SELL_SIGNAL} [{np_tl_1m[-1]}] [{np_cl_1m[-1]}]')


            ###########################################
            #####        SHORT POSITIONS       #######
            ###########################################


            ################################ SHORT SIGNAL ###########################

            SHORT_SELL_SIGNAL = bool_short_momentum and \
                                bool_downtrend_1m and \
                                not bool_closing_time \
                                and shorting_enabled

            # TODO: Check for support before selling

            logging.info(f'[{ticker}] short_sell_signal:   {SHORT_SELL_SIGNAL} [{np_tl_1m[-1]}] [{np_cl_1m[-1]}]')


            ################################ CLOSE SHORT SIGNAL #####################

            SHORT_BUY_SIGNAL = bool_buy_profit_target or \
                               (bool_close_short_momentum and bool_buy_price_below_sell and not bear_flag_1m) or \
                               (bool_buy_price_below_sell and bool_closing_time)

            logging.info(f'[{ticker}] short_buy_signal:   {SHORT_BUY_SIGNAL} [{np_tl_1m[-1]}] [{np_cl_1m[-1]}]')


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

            ################################ LONG BUY ###########################

            if not position and LONG_BUY_SIGNAL:  # if no position exists and a buy sig is found

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

                logging.info(f'[{ticker}] [long_buy_signal] buy_order_data: {buy_order_data}')

                buy_order_sent = False

                try:
                    buy_order_placed = requests.post(url=order_uri, headers=headers,
                                                     data=buy_order_data).json()
                    buy_order_sent = True
                    order_id = buy_order_placed['id']

                    logging.info(f"[{ticker}] [long_buy_signal] [buy_order_id] {order_id}")

                except Exception as e:
                    error_text = f'[ERROR] [{ticker}] [{np_tl_1m}] [{np_cl_1m}] [long_buy_signal] Error placing order: {str(e)}'
                    logging.info(error_text)
                    slackit(channel="ERROR", msg=error_text)

                buy_order_executed = False

                if buy_order_placed['status'] is not None:  # to check if order was placed

                    while not buy_order_executed:

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

                        time.sleep(10)  # WAIT 10 SECS BEFORE NEXT CHECK

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

                    logging.info(f'[{ticker}] [{np_cl_1m[-1]}] [{buy_price}] [{filled_at}]     '
                          f'[long_buy_signal]       {LONG_BUY_SIGNAL}            '
                          f'bool_buy_momentum    {bool_buy_momentum}          '
                          f'position    {position}[{position_qty}]             '
                          f'bool_closing_time     {bool_closing_time}          '
                          f'sell_target_based_on_profit_percentage [{sell_target_based_on_profit_percentage}]        ')

                    position = True # set position to True once BUY is executed
                else:
                    logging.error(f"[{current_ts}] [ERROR] {buy_order_details['side']} ORDER WAS NOT PLACED")


            ################################ LONG_SELL ###########################

            if position and position_side == 'long' and LONG_SELL_SIGNAL:

                sell_price = round(np_cl_1m[-2], 3)  # set sell price to 1 to 2 bars prior val
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

                logging.info(f'[{ticker}] [long_sell_signal] sell_order_data:    {sell_order_data}')

                sell_order_sent = False

                try:
                    sell_order_placed = requests.post(url=order_uri, headers=headers,
                                                      data=sell_order_data).json()
                    sell_order_sent = True
                    order_id = sell_order_placed['id']

                    logging.info(f"[{ticker}] [long_sell_signal] [sell_order_id] [{order_id}] ")

                except Exception as e:
                    error_text = f'[ERROR] [{ticker}] [{np_tl_1m}] [{np_cl_1m}] [long_sell_signal] Error placing order: {str(e)}'
                    logging.info(error_text)
                    slackit(channel="ERROR", msg=error_text)

                sell_order_executed = False

                # logging.info(f"SELL Order Placed Status Code:           {sell_order_placed['status_code']} ")

                if sell_order_placed['status'] is not None:

                    while not sell_order_executed:

                        # keep checking until order is filled

                        get_order_details_uri = f'{config.base_url}/orders/{order_id}'

                        sell_order_details = requests.get(url=get_order_details_uri, headers=headers).json()

                        waiting_to_sell = f"[{ticker}] [LONG_SELL_SIGNAL] [SELL] [WAITING_TO_EXECUTE] [{sell_order_details['submitted_at']}] " \
                            f"[{sell_order_details['status']}] {sell_order_details['side']} " \
                            f"order for {sell_order_details['qty']} shares of {sell_order_details['symbol']}"

                        logging.info(waiting_to_sell)

                        # slackit(channel='apca-paper', msg=waiting_to_sell)

                        if sell_order_details['status'] == 'filled':  # or order_details.status == 'partially_filled':
                            sell_order_executed = True

                        logging.info(f"[{ticker}] [LONG_SELL_SIGNAL] SELL ORDER STATUS:   {sell_order_placed['status']} ")

                        time.sleep(10)  # WAIT 10 SECS BEFORE NEXT CHECK

                    ###############
                    sell_price = round(float(sell_order_details['filled_avg_price']), 2)
                    ###############

                    filled_at = sell_order_details['filled_at']

                    side = str(sell_order_details['side']).upper()

                    profit = round((float(sell_price - buy_price) * position_qty), 2)

                    sell_order_text = f'[{ticker}] [LONG_SELL_SIGNAL] [{filled_at}] [EXECUTED] {side} ORDER WAS EXECUTED @ {sell_price}'

                    logging.info(sell_order_text)

                    # slackit(channel='apca_paper', msg=sell_order_text)  # post to slack

                    trade_text = f'[{ticker}] [LONG] [{current_ts}] BUY {position_qty} @ ${buy_price} SELL @ ${sell_price} \n PNL ${profit}'

                    slackit(channel=config.slack_channel, msg=trade_text)    # post to slack

                # signals.append(signal)

                logging.info(f'[{ticker}] [{np_tl_1m[-1]}] [{sell_price}]     '
                      f'[long_sell_signal]      {LONG_SELL_SIGNAL}            '
                      f'MOMENbool_sell_momentumTUM    {bool_sell_momentum}         '
                      f'position    {position}              '
                      f'bool_closing_time     {bool_closing_time}          '
                      f'sell_target_based_on_profit_percentage [{sell_target_based_on_profit_percentage}] {bool_sell_profit_target}  '
                      f'bool_sell_price_above_buy       {bool_sell_price_above_buy}')

                position = False  # set position to false once a sale has completed





            ################################ SHORT SELL ###########################

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

                logging.info(f'[{ticker}] [short_sell_signal] sell_order_data:    {sell_order_data}')

                sell_order_sent = False

                try:
                    sell_order_placed = requests.post(url=order_uri, headers=headers,
                                                      data=sell_order_data).json()
                    sell_order_sent = True
                    order_id = sell_order_placed['id']

                    logging.info(f"[{ticker}] [short_sell_signal] [sell_order_id] [{order_id}] ")

                except Exception as e:
                    error_text = f'[ERROR] [{ticker}] [{np_tl_1m}] [{np_cl_1m}] [short_sell_signal] Error placing order: {str(e)}'
                    logging.info(error_text)
                    slackit(channel="ERROR", msg=error_text)


                sell_order_executed = False

                # logging.info(f"SELL Order Placed Status Code:           {sell_order_placed['status_code']} ")

                if sell_order_placed['status'] is not None:

                    while not sell_order_executed:

                        # keep checking until order is filled

                        get_order_details_uri = f'{config.base_url}/orders/{order_id}'

                        sell_order_details = requests.get(url=get_order_details_uri, headers=headers).json()

                        waiting_to_sell = f"[{ticker}] [SHORT_SELL_SIGNAL] [SELL] [WAITING_TO_EXECUTE] [{sell_order_details['submitted_at']}] " \
                            f"[{sell_order_details['status']}] {sell_order_details['side']} " \
                            f"order for {sell_order_details['qty']} shares of {sell_order_details['symbol']}"

                        logging.info(waiting_to_sell)

                        # slackit(channel='apca-paper', msg=waiting_to_sell)

                        if sell_order_details['status'] == 'filled':  # or order_details.status == 'partially_filled':
                            sell_order_executed = True

                        logging.info(f"[{ticker}] [SHORT_SELL_SIGNAL] SELL ORDER STATUS:   {sell_order_placed['status']} ")

                        time.sleep(5)  # WAIT 10 SECS BEFORE NEXT CHECK

                    ###############
                    sell_price = round(float(sell_order_details['filled_avg_price']), 2)
                    ###############

                    buy_target_based_on_profit_percentage = sell_price - (
                            sell_price * profit_percentage) - price_delta # [shorting, buy even lower than sell price]

                    filled_at = sell_order_details['filled_at']

                    side = str(sell_order_details['side']).upper()

                    sell_order_text = f'[{ticker}] [SHORT_SELL_SIGNAL] [{filled_at}] [EXECUTED] {side} ORDER WAS EXECUTED @ {sell_price}'

                    logging.debug(sell_order_text)

                    # post to slack

                    slackit(channel=config.slack_channel, msg=sell_order_text)    # post to slack

                # signals.append(signal)

                logging.info(f'[{ticker}] [{np_tl_1m[-1]}] [{sell_price}]     '
                      f'[SHORT_SELL_SIGNAL]      {SHORT_SELL_SIGNAL}            '
                      f'bool_short_momentum    {bool_short_momentum}         '
                      f'position    {position}              '
                      f'bool_closing_time     {bool_closing_time}          '
                      f'buy_target_based_on_profit_percentage [{buy_target_based_on_profit_percentage}] {bool_buy_profit_target}  '
                      f'bool_buy_price_below_sell       {bool_buy_price_below_sell}')

                position = True  # set position to false once short sell is initiated

            ################################ SHORT BUY ###########################

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

                logging.debug(f'[{ticker}] [short_buy_signal] buy_order_data: {buy_order_data}')

                buy_order_sent = False

                try:
                    buy_order_placed = requests.post(url=order_uri, headers=headers,
                                                     data=buy_order_data).json()
                    buy_order_sent = True
                    order_id = buy_order_placed['id']

                    logging.info(f"[{ticker}] [short_buy_signal] [buy_order_id] {order_id}")

                except Exception as e:
                    error_text = f'[ERROR] [{ticker}] [{np_tl_1m}] [{np_cl_1m}] [short_buy_signal] Error placing order: {str(e)}'
                    logging.info(error_text)
                    slackit(channel="ERROR", msg=error_text)

                buy_order_executed = False

                if buy_order_placed['status'] is not None:  # to check if order was placed

                    while not buy_order_executed:

                        # keep checking until order is filled
                        # buy_order_details_data = {'order_id': order_id}
                        # buy_order_details_data = json.dumps(buy_order_details_data)

                        get_order_details_uri = f'{config.base_url}/orders/{order_id}'

                        buy_order_details = requests.get(url=get_order_details_uri, headers=headers).json()

                        logging.info(f"[{ticker}] [SHORT_BUY_SIGNAL] [BUY] [WAITING_TO_EXECUTE] [{buy_order_details['submitted_at']}] "
                              f"[{buy_order_details['status']}] {buy_order_details['side']} "
                              f"order for {buy_order_details['qty']} shares of {buy_order_details['symbol']}")

                        if buy_order_details['status'] == 'filled':  # or order_details.status == 'partially_filled':
                            buy_order_executed = True

                        logging.info(f"[{ticker}] [SHORT_BUY_SIGNAL] BUY_ORDER_STATUS:    {buy_order_placed['status']} ")

                        time.sleep(5)  # WAIT 5 SECS BEFORE NEXT CHECK

                    ###############
                    buy_price = float(buy_order_details['filled_avg_price'])  # ACTUAL FROM BUY ORDER
                    ###############

                    filled_at = buy_order_details['filled_at']
                    filled_qty = buy_order_details['filled_qty']

                    # # TODO: [IMPORTANT] Use actual fill price to derive sell_target_based_on_profit_percentage

                    buy_order_text = f"[{ticker}] [SHORT_BUY_SIGNAL] [{filled_at}] {str(buy_order_details['side']).upper()} ORDER OF {filled_qty} [{ticker}] EXECUTED @ {buy_price}"

                    logging.debug(buy_order_text)

                    profit = round((float(sell_price - buy_price) * position_qty), 2)   # shorting profit reversed

                    trade_text = f'[{ticker}] [SHORT] [{current_ts}] SELL {position_qty} @ ${sell_price} BUY @ ${buy_price} \n PNL ${profit}'

                    slackit(channel=config.slack_channel, msg=trade_text)    # post to slack

                    # post to slack

                    logging.info(f'[{ticker}] [SHORT_BUY_SIGNAL] [{np_cl_1m[-1]}] [{buy_price}] [{filled_at}]     '
                          f'[SHORT_BUY_SIGNAL]       {SHORT_BUY_SIGNAL}            '
                          f'bool_close_short_momentum    {bool_close_short_momentum}          '
                          f'position    {position}[{position_qty}]             '
                          f'bool_closing_time     {bool_closing_time}          '
                          f'buy_target_based_on_profit_percentage [{buy_target_based_on_profit_percentage}]        ')

                    position = False # set position to True once BUY is executed
                else:
                    logging.error(f"[{current_ts}] [SHORT_BUY_SIGNAL] [ERROR] {buy_order_details['side']} ORDER WAS NOT PLACED")



        # HEALTH CHECK

        if health_check_alert_counter == 1:
            msg = f'[CHECK] [{current_ts}] [{ticker}] OK'
            slackit(channel="CHECK", msg=msg)                    # Post to health-check slack channel
        elif health_check_alert_counter > 120:
            health_check_alert_counter = 0

        health_check_alert_counter += 1

        # HEALTH COUNTER END

        secs_to_sleep = 30

        x += 1

        # logging.info('\n')
        logging.info('--'*40)
        time.sleep(int(secs_to_sleep))


