
live_trade = False  # SET TO TRUE WHEN TRADING LIVE!!!


api_version = 'v2'
data_api_version = 'v1'


slack_message_prefix = ''

if live_trade: # LIVE!!!

    APCA_LIVE_BASE_URL = 'https://api.alpaca.markets'
    APCA_API_KEY_ID = " "
    APCA_API_SECRET_KEY = " "
    base_url = f'{APCA_LIVE_BASE_URL}/{api_version}'
    slack_live_url = "https://hooks.slack.com/services/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"  # ADD BEFORE RUNNLING LIVE!
    slack_message_prefix = 'LIVE'
else:   # PAPER TRADE

    APCA_PAPER_BASE_URL = 'https://paper-api.alpaca.markets'
    APCA_API_KEY_ID = 'PKFHKU5WPITCCK6NMDS9'
    APCA_API_SECRET_KEY = 'x1OTvpkGxqNUCSN1WWBOnOxM8rfTKSC0N6ZFdKUO'
    base_url = f'{APCA_PAPER_BASE_URL}/{api_version}'
    slack_paper_url = "https://hooks.slack.com/services/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"
    slack_message_prefix = 'PAPER'

# TODO: CHANGE BASE URL TO POINT TO PROD WHEN READY FOR LIVE TRADE


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


# Position sizing
position_size = 0.5

# time left for market to close
closing_window = 60     # in Minutes

# profit taking percentage - used in a sell signal
profit_percentage = 0.1  # 10%



account_uri = f'{base_url}/account'
order_uri = f'{base_url}/orders'
clock_uri = f'{base_url}/clock'
data_url = f'https://data.alpaca.markets/{data_api_version}'
slack_health_check_url = "https://hooks.slack.com/services/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"








############ BACKTEST ONLY ##################

tickers = ['V'] # for backtest algo_01.py
# num bars to fetch per time window
limit_1m = 350
limit_5m = 78
limit_15m = 29

paper_limit_1m = 100
paper_limit_5m = 100
paper_limit_15m = 100

