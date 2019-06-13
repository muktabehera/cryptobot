
live_trade = False                  # SET TO TRUE WHEN TRADING LIVE!!!

testing_algo_after_hours = True    # Set to False ALWAYS unless testing after hours

# data_provider = 'alpaca'          # polygon or alpaca
data_provider = 'polygon'           # polygon or alpaca

api_version = 'v2'

if data_provider == 'alpaca':
    data_api_version = 'v1'
    data_url = f'https://data.alpaca.markets/{data_api_version}'

if data_provider == 'polygon':
    data_api_version = 'v1'
    data_url = f'https://api.polygon.io/{data_api_version}/historic/agg'

    #     https://api.polygon.io/v1/historic/agg/minute/V?apiKey=PKYB9N5TQPSMNG5SLYNS&limit=3

day_trade_minimum = 0.00                    # this can be set to 25000.00 to keep min balance to avoid PDT flag

max_open_positions_allowed = 5              # Use to divide total equity among X max allowed open positions
closing_window = 60                         # time left for market to close

secs_to_sleep = 10                          # time between reruns if market is open.
profit_percentage = 0.02                    # profit taking percentage - used in a sell signal - updated to 10% test squeeze
price_delta = 0                             # use either profit percentage or price delta

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
    APCA_API_KEY_ID = 'PKHUBU9MNWKGTQ6IHG9U'
    APCA_API_SECRET_KEY = 'z2LqwS12BHjtPYfqOfMwHtSxvVhdYRNQFWPGHni1'
    base_url = f'{APCA_PAPER_BASE_URL}/{api_version}'
    slack_channel = 'PAPER'

# TODO: CHANGE BASE URL TO POINT TO PROD WHEN READY FOR LIVE TRADE


account_uri = f'{base_url}/account'
order_uri = f'{base_url}/orders'
clock_uri = f'{base_url}/clock'


# Top Popular Large and Mid Cap stocks on Robinhood

ticker = {
    "MSFT": "MSFT",
    "AMZN": "AMZN",
    "AAPL": "AAPL",
    "GOOG": "GOOG",
    "FB"  : "FB",
    "BRK.": "BRK.B",
    "BABA": "BABA",
    "TCEH": "TCEHY",
    "V"   :  "V",
    "JPM" :  "JPM",
    "WMT" :  "WMT",
    "BAC" :  "BAC",
    "CSCO": "CSCO",
    "DIS" :  "DIS",
    "PFE" :  "PFE",
    "T"   :  "T",
    "BA"  : "BA",
    "NFLX": "NFLX",
    "PYPL": "PYPL",
    "NKE" :  "NKE",
    "CRM" :  "CRM",
    "COST": "COST",
    "NVDA": "NVDA",
    "GE"  : "GE",
    "QCOM": "QCOM",
    "UBER": "UBER",
    "CVS" :  "CVS",
    "SNE" :  "SNE",
    "GM"  : "GM",
    "MU"  : "MU",
    "ATVI": "ATVI",
    "JD"  : "JD",
    "SHOP": "SHOP",
    "NOK" :  "NOK",
    "SIRI": "SIRI",
    "SPOT": "SPOT",
    "TWLO": "TWLO",
    "LYFT": "LYFT",
    "CGC" :  "CGC",
    "ROKU": "ROKU",
    "DBX" :  "DBX",
    "VZ"  : "VZ",
    "KO"  : "KO",
    "SBUX": "SBUX",
    "SQ"  : "SQ",
    "LUV" :  "LUV"
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

