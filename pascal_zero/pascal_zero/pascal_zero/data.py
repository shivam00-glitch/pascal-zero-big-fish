import pandas as pd

def normalize_ohlcv(df):
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    rename = {}
    for c in df.columns:
        if c in ['date','time','datetime','date_time']:
            rename[c] = 'timestamp'
        elif c in ['o']:
            rename[c] = 'open'
        elif c in ['h']:
            rename[c] = 'high'
        elif c in ['l']:
            rename[c] = 'low'
        elif c in ['c','close_price','last']:
            rename[c] = 'close'
        elif c in ['vol','qty']:
            rename[c] = 'volume'
    df = df.rename(columns=rename)
    if 'timestamp' not in df.columns:
        raise ValueError("CSV la 'timestamp' column illa")
    if 'close' not in df.columns:
        raise ValueError("CSV la 'close' column illa")
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['timestamp','close'])
    df = df.sort_values('timestamp')
    for col in ['open','high','low','close','volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df['close'] = df['close'].ffill().bfill()
    return df.reset_index(drop=True)

def load_csv(file):
    try:
        df = pd.read_csv(file)
    except Exception as e:
        raise ValueError(f"CSV read panna mudiyala: {e}")
    return normalize_ohlcv(df)
