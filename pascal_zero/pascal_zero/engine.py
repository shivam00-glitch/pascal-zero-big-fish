import pandas as pd
import numpy as np

def calculate(df, length=10, smooth=3):
    df = df.copy()
    df = df.sort_values("timestamp").reset_index(drop=True)
    
    close = pd.to_numeric(df["close"], errors='coerce')
    close = close.ffill().bfill().values
    
    n = len(df)
    x = np.arange(length)
    x_mean = x.mean()
    denom = ((x - x_mean)**2).sum()
    
    slopes = []
    for i in range(n):
        if i < length-1:
            slopes.append(0.0)
        else:
            y = close[i-length+1:i+1]
            y_mean = y.mean()
            slope = ((x - x_mean)*(y - y_mean)).sum() / denom if denom != 0 else 0.0
            slopes.append(float(slope))
    
    df["pascal_value"] = pd.Series(slopes).rolling(smooth, min_periods=1).mean()
    
    pv = df["pascal_value"]
    prev = pv.shift(1)
    df["buy_signal"] = (prev <= 0) & (pv > 0)
    df["buy_signal"] = df["buy_signal"].fillna(False)
    df["exit_signal"] = (prev >= 0) & (pv < 0)
    df["exit_signal"] = df["exit_signal"].fillna(False)
    df["cycle_duration"] = np.nan

    last_buy_t = None
    last_buy_idx = None
    for idx in df.index:
        if df.loc[idx, "buy_signal"]:
            if last_buy_t is None:
                if idx == 0:
                    f_buy = 1.0
                else:
                    v0 = df.loc[idx-1, "pascal_value"]
                    v1 = df.loc[idx, "pascal_value"]
                    d = (v1 - v0)
                    f_buy = -v0/d if d != 0 else 1.0
                    f_buy = max(0.0, min(1.0, f_buy))
                last_buy_t = (idx-1 + f_buy) if idx > 0 else float(idx)
                last_buy_idx = idx
        if df.loc[idx, "exit_signal"] and last_buy_t is not None:
            v0 = df.loc[idx-1, "pascal_value"] if idx > 0 else 0
            v1 = df.loc[idx, "pascal_value"]
            d = (v0 - v1)
            f_exit = v0/d if d != 0 else 1.0
            f_exit = max(0.0, min(1.0, f_exit))
            t_exit = (idx-1 + f_exit) if idx > 0 else float(idx)
            dur = t_exit - last_buy_t
            if dur < 0:
                dur = float(idx - last_buy_idx)
            dur = round(dur*4)/4.0
            df.loc[idx, "cycle_duration"] = dur
            last_buy_t = None
            last_buy_idx = None
    return df

def summarize_trades(result):
    buy_count = int(result["buy_signal"].sum()) if "buy_signal" in result.columns else 0
    completed = int(result["cycle_duration"].notna().sum()) if "cycle_duration" in result.columns else 0
    mean_dur = float(result["cycle_duration"].mean()) if completed > 0 else None
    return {"buy_count": buy_count, "completed_cycles": completed, "mean_duration": mean_dur}
