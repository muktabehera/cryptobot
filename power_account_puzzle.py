'''

Let:
S = query_Alpaca_data_API('SPY', 'day', '2018')
D = query_Alpaca_data_API('DIA', 'day', '2018')

Find X where:
is_prime(int(S[X].close * 10**2)) => True
is_prime(int(D[X].close * 10**2)) => True
dayofweek(trading_2018[X]) => Thursday

'''

import requests
import config
import dateutil
import pytz
import pandas as pd
import numpy as np
from datetime import datetime


nyc = pytz.timezone('America/New_York')

headers = {
    "APCA-API-KEY-ID": config.APCA_API_KEY_ID,
    "APCA-API-SECRET-KEY": config.APCA_API_SECRET_KEY,
    "Content-Type": "application/json"
}


def query_Alpaca_data_API(ticker, period, year):

    data = list()
    cl_1D = list()
    np_cl_1D = np.array([])

    bar_interval = "1Day"
    payload_1D = {
        "symbols": ticker,
        "limit": 365,
        "start": f"{year}-01-01",
        "end": f"{year}-12-31",
    }
    base_uri_1D = f'https://data.alpaca.markets/v1/bars/{bar_interval}'
    bars_1D = requests.get(url=base_uri_1D, params=payload_1D, headers=headers).json()

    for i, v1m in enumerate(bars_1D[ticker]):
        cl_1D.append(v1m['c'])
        np_cl_1D = np.array(cl_1D)

    # logging.info(f'np_tl_1m    {len(np_tl_1m)}  np_cl_1m    {len(np_cl_1m)}')

    data = {
        "np_cl_1D": np_cl_1D,
    }

    return data


def is_prime(n):
    for i in range(3, n):
        if n % i == 0:
            return False
    return True


if __name__ == '__main__':

    S = query_Alpaca_data_API('SPY', 'day', '2018')
    D = query_Alpaca_data_API('DIA', 'day', '2018')

    for X,V in enumerate(S):

        if is_prime(int(S[X].close * 10 ** 2)):
            print(f"X, S[{X}] = {V}")

    for X, V in enumerate(D):

        if is_prime(int(D[X].close * 10 ** 2)):
            print(f"X, D[{X}] = {V}")

    # dayofweek(trading_2018[X]) => Thursday

    # datetime.date( 2010 , 6 , 16 ).strftime( "%A" )





