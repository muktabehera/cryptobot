
live_trade = False  # SET TO TRUE WHEN TRADING LIVE!!!

api_version = 'v2'
data_api_version = 'v1'

if live_trade: # LIVE!!!

    APCA_LIVE_BASE_URL = 'https://api.alpaca.markets'
    APCA_API_KEY_ID = " "
    APCA_API_SECRET_KEY = " "
    base_url = f'{APCA_LIVE_BASE_URL}/{api_version}'

else:   # PAPER TRADE

    APCA_PAPER_BASE_URL = 'https://paper-api.alpaca.markets'
    APCA_API_KEY_ID = 'PKFHKU5WPITCCK6NMDS9'
    APCA_API_SECRET_KEY = 'x1OTvpkGxqNUCSN1WWBOnOxM8rfTKSC0N6ZFdKUO'

    base_url = f'{APCA_PAPER_BASE_URL}/{api_version}'

# TODO: CHANGE BASE URL TO POINT TO PROD WHEN READY FOR LIVE TRADE


# PAPER ALGO PARAMETERS

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

# ticker = "MSFT"

# bar_interval = 1    # trade every 1 min or 5

position_size = 0.25


account_uri = f'{base_url}/account'
order_uri = f'{base_url}/orders'
clock_uri = f'{base_url}/clock'


paper_limit_1m = 100
paper_limit_5m = 100
paper_limit_15m = 100


# time left for market to close
closing_window = 60     # in Minutes

# profit taking percentage - used in a sell signal
profit_percentage = 0.1  # 10%


############ BACKTEST ONLY ##################
tickers = ['V'] # for backtest algo_01.py
# num bars to fetch per time window
limit_1m = 350
limit_5m = 78
limit_15m = 29

########## SLACK WEBOOOK

apca_paper = 'https://hooks.slack.com/services/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'
health_check = 'https://hooks.slack.com/services/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'
apca_live = ''  # FILL LATER

