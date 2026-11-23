import requests
import pandas as pd
from urllib.parse import quote
from datetime import date, timedelta

UPSTOX_SYMBOLS = {
    "NSE:NIFTY": "NSE_INDEX|Nifty 50",
    "NSE:NIFTYBANK": "NSE_INDEX|Nifty Bank",
    "NSE:RELIANCE": "NSE_EQ|INE002A01018",
    "NSE:TCS": "NSE_EQ|INE467B01029",
    "NSE:INFY": "NSE_EQ|INE009A01021",
    "NSE:HDFCBANK": "NSE_EQ|INE040A01034",
}

def get_broker_status():
    return "Upstox ready"

def fetch_upstox_candles(symbol: str, interval: str, access_token: str):
    instrument = UPSTOX_SYMBOLS.get(symbol.upper(), symbol)
    inst_enc = quote(instrument, safe='')
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

    if interval in ["1minute", "30minute"]:
        url = f"https://api.upstox.com/v2/historical-candle/intraday/{inst_enc}/{interval}"
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        candles = r.json()["data"]["candles"]
    else:
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=2)).isoformat()
        url = f"https://api.upstox.com/v2/historical-candle/{inst_enc}/{interval}/{today}/{yesterday}"
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        candles = r.json()["data"]["candles"]

    df = pd.DataFrame(candles, columns=["timestamp","open","high","low","close","volume","oi"])
    df = df[["timestamp","open","high","low","close","volume"]]
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df
