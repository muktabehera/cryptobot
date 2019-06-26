
live_trade = False                          # SET TO TRUE WHEN TRADING LIVE!!!

allow_shorting = True                       # SET False to Disable Shorting

testing_algo_after_hours = True            # Set to False ALWAYS unless testing after hours

# data_provider = 'alpaca'                  # polygon or alpaca
data_provider = 'polygon'                   # polygon or alpaca

api_version = 'v2'

day_trade_minimum = 0.00                    # this can be set to 25000.00 to keep min balance to avoid PDT flag

max_open_positions_allowed = 5              # Use to divide total equity among X max allowed open positions
closing_window = 120                        # time left for market to close

secs_to_sleep = 0                           # time between reruns if market is open or testing after hours.

profit_percentage = 0                       # profit taking percentage - used in a sell signal - updated to 10% test squeeze
price_delta = 0                             # use either profit percentage or price delta

if profit_percentage == 0:
    price_delta = 0.5       # 50 Cents

# Risk / Reward : 3/2
profit_threshold_to_close_position = 20     # in dollars, this will set the max profit in any position
loss_threshold_to_close_position = -30      # in $, THIS HAS TO BE -VE and will set the max loss in any position


# to avoid selling or buying too quickly when bool_sell_price_above_buy or bool_buy_price_below_sell are True
# adding a delta price component. This is different from price delta above
small_price_increment = 0.05    # 5 cents

# uptrend timeperiod sma_1m
timeperiod = 20


# Support - Resistance Params

sr_error_margin = 0.0       # price increment for errors, 10 cents
sr_percent_bounce = 0.05    # price bounced x %
sr_min_touches = 3          # price has tested x # times

# END SR Params

order_wait_counter = 10     # [REDACTED] max retries before you skip checking for an order status


if data_provider == 'alpaca':
    data_api_version = 'v1'
    data_url = f'https://data.alpaca.markets/{data_api_version}'

if data_provider == 'polygon':
    data_api_version = 'v1'
    data_url = f'https://api.polygon.io/{data_api_version}/historic/agg'

    #     https://api.polygon.io/v1/historic/agg/minute/V?apiKey=PKYB9N5TQPSMNG5SLYNS&limit=3

slack_channel = None

if live_trade:  # LIVE!!!

    APCA_LIVE_BASE_URL = 'https://api.alpaca.markets'
    APCA_API_KEY_ID = " "
    APCA_API_SECRET_KEY = " "
    base_url = f'{APCA_LIVE_BASE_URL}/{api_version}'
    slack_channel = 'LIVE'

else:   # PAPER TRADE

    APCA_PAPER_BASE_URL = 'https://paper-api.alpaca.markets'
    APCA_API_KEY_ID = 'PKPIND5FM8B0M8U7GOYD'
    APCA_API_SECRET_KEY = 'V70G6k6DOWc7Nx/SAoJSIT00UUQeMJk0mUWU3pLd'
    base_url = f'{APCA_PAPER_BASE_URL}/{api_version}'
    slack_channel = 'PAPER'

# TODO: CHANGE BASE URL TO POINT TO PROD WHEN READY FOR LIVE TRADE


account_uri = f'{base_url}/account'
order_uri = f'{base_url}/orders'
clock_uri = f'{base_url}/clock'
positions_uri = f'{base_url}/positions'


# Top Popular Large and Mid Cap stocks on Robinhood

tickers = {
    "1": ["MSFT", "AAPL", "FB", "BRK.B", "BABA", "V", "JPM", "WMT", "BAC", "CSCO", "DIS", "PFE", "T",
          "BA", "NFLX", "PYPL", "NKE", "CRM", "COST", "NVDA", "GE", "QCOM", "CVS", "SNE", "GM", "MU", "ATVI", "JD",
          "NOK", "DBX", "SPOT", "TWLO", "VZ", "KO", "SBUX", "LUV", "CTSH", "ADBE", "ACN"],

    "2": ["V", "MSFT", "CRM", "BABA"],

    "3": [],

    "4": [],

    "5": ["LYFT", "WORK", "CGC", "SHOP", "SIRI", "ROKU", "SQ", "TSLA", "UBER"]   # can't be short sold
}

    # "UBER": "UBER",       # Not supported by Alpaca Data Feed


limit_1m = 360     # ~6 Hours i.e the number of last bars to fetch for each symbol for backtesting and signal generation
# limit_5m = 100
# limit_15m = 100


############ BACKTEST ONLY ##################

paper_tickers = ['V'] # for backtest algo_01.py
# num bars to fetch per time window
paper_limit_1m = 350
paper_limit_5m = 78
paper_limit_15m = 29
############ BACKTEST ONLY ##################
