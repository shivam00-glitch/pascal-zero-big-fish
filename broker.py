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

    # Upstox direct-a 5minute,15minute kudukaadhu
    need_resample = False
    resample_rule = None
    base = interval

    if interval == "5minute":
        base = "1minute"
        need_resample = True
        resample_rule = "5min"
    elif interval == "15minute":
        base = "1minute"
        need_resample = True
        resample_rule = "15min"
    elif interval not in ["1minute", "30minute", "day"]:
        base = "1minute"

    to_date = date.today()
    from_date = to_date - timedelta(days=7)
    url = f"https://api.upstox.com/v2/historical-candle/{inst_enc}/{base}/{to_date}/{from_date}"

    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    candles = r.json()["data"]["candles"]

    df = pd.DataFrame(candles, columns=["timestamp","open","high","low","close","volume","oi"])
    df = df[["timestamp","open","high","low","close","volume"]]
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    if need_resample:
        df = df.set_index("timestamp").resample(resample_rule).agg({
            "open":"first","high":"max","low":"min","close":"last","volume":"sum"
        }).dropna().reset_index()

    df = df.sort_values("timestamp").reset_index(drop=True)
    return df
