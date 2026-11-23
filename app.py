import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from engine import calculate, summarize_trades
from data import normalize_ohlcv, load_csv
from broker import get_broker_status, fetch_live_candles

st.set_page_config(page_title="PASCAL ZERO | BIG FISH", page_icon="〽️", layout="wide")
st.title("〽️ PASCAL ZERO — BIG FISH")
st.caption("Independent zero-line research & backtesting workstation")

with st.sidebar:
    st.header("Engine settings")
    length = st.slider("Momentum lookback", 3, 50, 10)
    smooth = st.slider("Smoothing", 1, 15, 3)
    symbol_input = st.text_input("Symbol / Instrument", "NSE:NIFTYBANK")
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
    st.info("Broker adapter is ready to be connected.")
    st.write("Adapter status:", get_broker_status())
    broker = st.selectbox("Broker", ["Not selected", "Zerodha Kite Connect", "Upstox", "Angel One", "Other"])
    symbol_input = st.text_input("Instrument / symbol", symbol_input)
    interval = st.selectbox("Candle interval", ["1minute", "3minute", "5minute", "15minute", "day"], index=2)
    if st.button("Check live adapter"):
        st.warning("No broker credentials configured yet.")
    df = None

if df is None:
    st.markdown("### CSV format")
    st.code("timestamp,open,high,low,close,volume\n2026-11-20 09:15,63000,63100,62950,63080,125000", language="csv")
    st.markdown("""
    **How to start**
    1. Export historical OHLCV candles from your broker.
    2. Upload the CSV above.
    3. Review candle + volume + Pascal oscillator.
    """)
    st.stop()

# Ensure OHLC columns exist
for col in ["open", "high", "low", "close"]:
    if col not in df.columns:
        df[col] = df["close"]
if "volume" not in df.columns:
    df["volume"] = 0

result = calculate(df, length=length, smooth=smooth)
stats = summarize_trades(result)

# Stock / Index details header
last_close = float(result["close"].iloc[-1])
first_open = float(result["open"].iloc[0])
day_high = float(result["high"].max())
day_low = float(result["low"].min())
total_vol = float(result["volume"].sum())
prev_close = float(result["close"].iloc[-2]) if len(result) > 1 else last_close
chg = last_close - first_open
pct = (chg / first_open * 100) if first_open != 0 else 0.0
last_pascal = float(result["pascal_value"].iloc[-1])
state = "ABOVE ZERO" if last_pascal > 0 else "BELOW ZERO"
start_t = result["timestamp"].iloc[0]
end_t = result["timestamp"].iloc[-1]

st.subheader(f"{symbol_input}  •  {len(result)} candles")
st.caption(f"{start_t} → {end_t}")

a,b,c,d = st.columns(4)
a.metric("Last Price", f"{last_close:,.2f}", f"{chg:+.2f} ({pct:+.2f}%)")
b.metric("Day High / Low", f"{day_high:,.2f}", f"Low {day_low:,.2f}")
c.metric("Total Volume", f"{total_vol:,.0f}")
d.metric("Pascal Value", f"{last_pascal:.2f}", state)

e,f,g = st.columns(3)
e.metric("BUY signals", stats["buy_count"])
f.metric("Completed cycles", stats["completed_cycles"])
g.metric("Mean BUY → down-cross", f"{stats['mean_duration']:.2f}" if stats["mean_duration"] is not None else "—")

# TradingView like 3-panel chart
fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
    row_heights=[0.5, 0.15, 0.35], vertical_spacing=0.05,
    subplot_titles=(f"{symbol_input} - Price", "Volume", "PASCAL ZERO Oscillator"))

fig.add_trace(go.Candlestick(
    x=result["timestamp"], open=result["open"], high=result["high"],
    low=result["low"], close=result["close"], name="Price"), row=1, col=1)

fig.add_trace(go.Bar(x=result["timestamp"], y=result["volume"], name="Volume"), row=2, col=1)

fig.add_trace(go.Scatter(x=result["timestamp"], y=result["pascal_value"],
    name="PASCAL VALUE", line=dict(width=2)), row=3, col=1)

fig.add_hline(y=0, line_width=1, row=3, col=1)

buys = result[result["buy_signal"]]
exits = result[result["exit_signal"]]
fig.add_trace(go.Scatter(x=buys["timestamp"], y=buys["pascal_value"],
    mode="markers", name="BUY", marker=dict(symbol="triangle-up", size=11)), row=3, col=1)
fig.add_trace(go.Scatter(x=exits["timestamp"], y=exits["pascal_value"],
    mode="markers", name="ZERO DOWN-CROSS", marker=dict(symbol="triangle-down", size=10)), row=3, col=1)

fig.update_layout(height=700, template="plotly_dark",
    margin=dict(l=10,r=10,t=40,b=10),
    xaxis_rangeslider_visible=False, showlegend=True)
fig.update_yaxes(title_text="Price", row=1, col=1)
fig.update_yaxes(title_text="Vol", row=2, col=1)
fig.update_yaxes(title_text="Oscillator", row=3, col=1)
fig.update_xaxes(title_text="Time", row=3, col=1)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Signal & duration log")
cols = ["timestamp", "close", "pascal_value", "buy_signal", "exit_signal", "cycle_duration"]
view = result[cols].copy()
view = view[(view["buy_signal"]) | (view["exit_signal"]) | (view["cycle_duration"].notna())].tail(100)
st.dataframe(view.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)

st.subheader("Method notes")
st.warning("Research prototype only. Backtest results do not predict future performance.")
