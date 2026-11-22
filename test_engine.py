import pandas as pd
from pascal_zero.engine import calculate, summarize_trades

def test_engine_returns_required_columns():
    close = [10, 9, 8, 9, 10, 12, 13, 12, 11, 10, 9, 8, 7, 8, 9, 11, 12]
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=len(close), freq="5min"),
        "open": close, "high": [x+1 for x in close], "low": [x-1 for x in close],
        "close": close, "volume": [1000]*len(close)
    })
    result = calculate(df, length=3, smooth=1)
    for col in ["pascal_value", "buy_signal", "exit_signal", "cycle_duration"]:
        assert col in result.columns
    stats = summarize_trades(result)
    assert stats["buy_count"] >= 0
