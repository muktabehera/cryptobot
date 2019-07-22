import requests
from archive import config

url = f'https://data.alpaca.markets/v2/bars/1Min'

headers = {
    "APCA-API-KEY-ID": config.APCA_API_KEY_ID,
    "APCA-API-SECRET-KEY": config.APCA_API_SECRET_KEY,
    "Content-Type": "application/json"
}

payload = {
    "symbols": "V",
    "limit": "10",
}

response = requests.get(url=url, headers=headers, params=payload).json()

print(response)

