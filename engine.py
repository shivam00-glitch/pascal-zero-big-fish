import numpy as np
import pandas as pd

def _linreg_endpoint(series: pd.Series, length: int) -> pd.Series:
    x = np.arange(length, dtype=float)
    x_mean = x.mean()
    denom = ((x - x_mean) ** 2).sum()
    def endpoint(values):
        y = np.asarray(values, dtype=float)
        if np.isnan(y).any():
            return np.nan
        slope = ((x - x_mean) * (y - y.mean())).sum() / denom
        intercept = y.mean() - slope * x_mean
        return intercept + slope * (length - 1)
    return series.rolling(length, min_periods=length).apply(endpoint, raw=True)

def calculate(df: pd.DataFrame, length: int = 10, smooth: int = 3) -> pd.DataFrame:
    out = df.copy().reset_index(drop=True)
    lr = _linreg_endpoint(out["close"], length)
    # First difference of regression endpoint is the momentum oscillator.
    raw = lr.diff()
    out["pascal_value"] = raw.rolling(smooth, min_periods=smooth).mean()
    prev = out["pascal_value"].shift(1)
    cur = out["pascal_value"]
    out["buy_signal"] = (prev <= 0) & (cur > 0)
    out["exit_signal"] = (prev >= 0) & (cur < 0)
    out["buy_signal"] = out["buy_signal"].fillna(False)
    out["exit_signal"] = out["exit_signal"].fillna(False)
    out["cycle_duration"] = np.nan

    active_buy_index = None
    for i in range(len(out)):
        if bool(out.at[i, "buy_signal"]):
            active_buy_index = i
        elif bool(out.at[i, "exit_signal"]) and active_buy_index is not None:
            # Estimate crossing point inside the current candle interval.
            p = abs(float(prev.iloc[i]))
            c = abs(float(cur.iloc[i]))
            frac = p / (p + c) if (p + c) else 0.5
            elapsed = max(0.0, (i - 1 - active_buy_index) + frac)
            rounded = round(elapsed * 4) / 4
            out.at[i, "cycle_duration"] = rounded
            active_buy_index = None
    return out

def summarize_trades(result: pd.DataFrame) -> dict:
    durations = result["cycle_duration"].dropna()
    return {
        "buy_count": int(result["buy_signal"].sum()),
        "completed_cycles": int(len(durations)),
        "mean_duration": float(durations.mean()) if len(durations) else None,
    }
