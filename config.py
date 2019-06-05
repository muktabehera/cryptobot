
live_trade = False  # SET TO TRUE WHEN TRADING LIVE!!!


api_version = 'v2'
data_api_version = 'v1'

position_size = 0.25        # Position sizing
closing_window = 120         # time left for market to close


profit_percentage = 0.1   # profit taking percentage - used in a sell signal - updated to 10% test squeeze
price_delta = 0             # use either profit percentage or price delta

if profit_percentage == 0:
    price_delta = 0.5       # 50 Cents

slack_channel = ''

if live_trade:  # LIVE!!!

    APCA_LIVE_BASE_URL = 'https://api.alpaca.markets'
    APCA_API_KEY_ID = " "
    APCA_API_SECRET_KEY = " "
    base_url = f'{APCA_LIVE_BASE_URL}/{api_version}'
    slack_channel = 'LIVE'

else:   # PAPER TRADE

    APCA_PAPER_BASE_URL = 'https://paper-api.alpaca.markets'
    APCA_API_KEY_ID = 'PK5DIJJLFSD5Z0YP3H7R'
    APCA_API_SECRET_KEY = 'JzV6SP6/yRq8emdMX2gwSxtbbIdr5gBybwZ0BU1V'
    base_url = f'{APCA_PAPER_BASE_URL}/{api_version}'
    slack_channel = 'PAPER'

# TODO: CHANGE BASE URL TO POINT TO PROD WHEN READY FOR LIVE TRADE


account_uri = f'{base_url}/account'
order_uri = f'{base_url}/orders'
clock_uri = f'{base_url}/clock'
data_url = f'https://data.alpaca.markets/{data_api_version}'

ticker = {
    "MSFT": "MSFT",
    "V":    "V",
    "AAPL": "AAPL",
    "NFLX": "NFLX",
    "AMZN": "AMZN",
    "GOOG": "GOOG",
    "CTSH": "CTSH",
    "FB":   "FB"
}


############ BACKTEST ONLY ##################

tickers = ['V'] # for backtest algo_01.py
# num bars to fetch per time window
limit_1m = 350
limit_5m = 78
limit_15m = 29

paper_limit_1m = 100
paper_limit_5m = 100
paper_limit_15m = 100

