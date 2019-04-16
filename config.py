
APCA_API_KEY_ID='PKE22M0NNY8M9ODO2R2T'
APCA_API_SECRET_KEY='uENB0q0q07XLDqhj/ICGjHC5ZWooijWBoxXg4FH5'
APCA_PAPER_BASE_URL='https://paper-api.alpaca.markets'
APCA_LIVE_BASE_URL='https://api.alpaca.markets'



#QUANDL https://www.quandl.com/account/profile
QUANDL_API_KEY='MnmET18nhTk3CNMA2WbM'


## SLACK WEBOOOK

apca_paper = 'https://hooks.slack.com/services/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'
health_check = 'https://hooks.slack.com/services/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'
apca_live = ''  # FILL LATER


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

bar_interval = 1    # trade every 1 min or 5

position_size = 0.25


account_uri = 'https://paper-api.alpaca.markets/v1/account'
order_uri = 'https://paper-api.alpaca.markets/v1/orders'
clock_uri = 'https://paper-api.alpaca.markets/v1/clock'

units_to_trade = 10


paper_limit_5m = 10
paper_limit_1m = 1000    # CHANGED TEMPORARILY, max allowed 1000
# time left for market to close
closing_window = 30
# profit taking percentage - used in a sell signal
profit_percentage = 0.02  # 10%


############ BACKTEST ONLY ##################
tickers = ['V'] # for backtest algo_01.py
# num bars to fetch per time window
limit_1m = 350
limit_5m = 78
limit_15m = 29

