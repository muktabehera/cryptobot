api_version = 'v3'
api_endpoint = f"https://api.bittrex.com/{api_version}"
api_key = b'6d708a64b3be46698beadcf2a70b5751'
api_secret = '5b3da6046b14418184e5b7cf097e04fd'

logging_level = 20  # https://docs.python.org/3/library/logging.html#logging-levels
#debug: 10, info: 20, warning: 30, error: 40,

marketsymbol = 'XRP-USD'
currencysymbol = 'XRP'

commission_percentage = 0.004
profit_target = 0.02      # % used as profit
per_resistance_threshold = 0.0005    # Negligible, but can be adjusted if needed

