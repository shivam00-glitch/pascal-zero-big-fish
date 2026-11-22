import pandas as pd

REQUIRED = {"open", "high", "low", "close", "volume"}

def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    aliases = {"date":"timestamp", "datetime":"timestamp", "time":"timestamp",
               "vol":"volume", "qty":"volume"}
    out = out.rename(columns=aliases)
    if "timestamp" not in out.columns:
        raise ValueError("CSV must contain timestamp/date/datetime column.")
    missing = REQUIRED - set(out.columns)
    if missing:
        raise ValueError("Missing OHLCV columns: " + ", ".join(sorted(missing)))
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    for col in REQUIRED:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["timestamp", "open", "high", "low", "close"])
    out = out.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
    if out.empty:
        raise ValueError("No valid candle rows found.")
    return out[["timestamp", "open", "high", "low", "close", "volume"]]

def load_csv(file_obj) -> pd.DataFrame:
    return normalize_ohlcv(pd.read_csv(file_obj))
