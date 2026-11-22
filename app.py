import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pascal_zero.engine import calculate, summarize_trades
from pascal_zero.data import normalize_ohlcv, load_csv
from pascal_zero.broker import get_broker_status, fetch_live_candles

st.set_page_config(page_title="PASCAL ZERO | BIG FISH", page_icon="〽️", layout="wide")
st.title("〽️ PASCAL ZERO — BIG FISH")
st.caption("Independent zero-line research & backtesting workstation")

with st.sidebar:
    st.header("Engine settings")
    length = st.slider("Momentum lookback", 3, 50, 10)
    smooth = st.slider("Smoothing", 1, 15, 3)
    st.divider()
    st.subheader("Data source")
    source = st.radio("Choose data", ["Upload CSV", "Broker API (adapter)"])
    st.caption("Live data requires a broker-specific adapter and credentials.")

df = None
if source == "Upload CSV":
    uploaded = st.file_uploader("Upload OHLCV CSV", type=["csv"])
    if uploaded:
        try:
            df = load_csv(uploaded)
            st.success(f"Loaded {len(df)} candles")
        except Exception as e:
            st.error(f"Could not read CSV: {e}")
else:
    st.info("Broker adapter is ready to be connected. Select your broker before enabling live market data.")
    st.write("Adapter status:", get_broker_status())
    broker = st.selectbox("Broker", ["Not selected", "Zerodha Kite Connect", "Upstox", "Angel One", "Other"])
    symbol = st.text_input("Instrument / symbol", "NSE:NIFTYBANK")
    interval = st.selectbox("Candle interval", ["1minute", "3minute", "5minute", "15minute", "day"], index=2)
    if st.button("Check live adapter"):
        st.warning("No broker credentials or broker-specific implementation configured yet. No live prices are being fetched.")

if df is None:
    st.markdown("### CSV format")
    st.code("timestamp,open,high,low,close,volume\n2026-11-20 09:15,63000,63100,62950,63080,125000", language="csv")
    st.markdown("""
    **How to start**
    1. Export historical OHLCV candles from your broker or a trusted data source.
    2. Upload the CSV above.
    3. Review the oscillator, zero-cross signals and estimated candle duration.
    """)
    st.stop()

result = calculate(df, length=length, smooth=smooth)
stats = summarize_trades(result)

a,b,c,d = st.columns(4)
a.metric("Latest Pascal Value", f"{result['pascal_value'].iloc[-1]:.5f}")
a.metric("Current State", "ABOVE ZERO" if result["pascal_value"].iloc[-1] > 0 else "BELOW ZERO")
b.metric("BUY signals", stats["buy_count"])
c.metric("Completed cycles", stats["completed_cycles"])
d.metric("Mean BUY → down-cross", f"{stats['mean_duration']:.2f}" if stats["mean_duration"] is not None else "—")

fig = go.Figure()
fig.add_trace(go.Scatter(x=result["timestamp"], y=result["pascal_value"], name="PASCAL VALUE", line=dict(width=2)))
fig.add_hline(y=0, line_dash="solid", line_width=1)
buys = result[result["buy_signal"]]
exits = result[result["exit_signal"]]
fig.add_trace(go.Scatter(x=buys["timestamp"], y=buys["pascal_value"], mode="markers", name="BUY", marker=dict(symbol="triangle-up", size=11)))
fig.add_trace(go.Scatter(x=exits["timestamp"], y=exits["pascal_value"], mode="markers", name="ZERO DOWN-CROSS", marker=dict(symbol="triangle-down", size=10)))
fig.update_layout(height=430, template="plotly_dark", margin=dict(l=10,r=10,t=30,b=10), xaxis_title="Time", yaxis_title="Oscillator")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Signal & duration log")
cols = ["timestamp", "close", "pascal_value", "buy_signal", "exit_signal", "cycle_duration"]
view = result[cols].copy()
view = view[(view["buy_signal"]) | (view["exit_signal"]) | (view["cycle_duration"].notna())].tail(100)
st.dataframe(view.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)

st.subheader("Method notes")
st.warning(
    "This is a research prototype, not a verified reproduction of your original PASCAL ZERO V1. "
    "The screenshot does not reveal the V1 formula. The current engine uses smoothed linear-regression "
    "slope of closing price. Fractional duration is estimated by linear interpolation between adjacent "
    "oscillator values and rounded to the nearest 0.25 candle."
)
st.caption("Signals are candle-close confirmed. Backtest results do not predict future performance.")
