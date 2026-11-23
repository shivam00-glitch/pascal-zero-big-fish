import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh
from engine import calculate, summarize_trades
from data import load_csv
from broker import UPSTOX_SYMBOLS, fetch_upstox_candles

st.set_page_config(page_title="PASCAL ZERO | BIG FISH", page_icon="〽️", layout="wide")

# ---- PRO DARK LOOK ----
st.markdown("""
<style>
[data-testid="stSidebar"] {background-color:#0e1117;}
.main-header {font-size:2.2rem; font-weight:800; color:#fafafa;}
.sub-header {color:#8b949e; margin-top:-12px;}
[data-testid="stMetric"] {background:#161b22; border:1px solid #30363d; border-radius:12px; padding:12px;}
[data-testid="stMetricValue"] {color:#58a6ff; font-size:1.5rem;}
[data-testid="stMetricLabel"] {color:#c9d1d9;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">〽️ PASCAL ZERO — BIG FISH</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Live momentum workstation • Powered by Upstox</div>', unsafe_allow_html=True)

IST = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(IST)
market_open = (now_ist.weekday() < 5) and (time(9,15) <= now_ist.time() <= time(15,30))

with st.sidebar:
    st.header("⚙️ Engine")
    length = st.slider("Momentum lookback", 3, 50, 10)
    smooth = st.slider("Smoothing", 1, 15, 3)
    st.divider()
    source = st.radio("Data source", ["Upstox Live", "Upload CSV"])

if market_open and source == "Upstox Live":
    st_autorefresh(interval=60000, key="liverefresh")
    st.sidebar.success("🟢 LIVE • Auto refresh ON (60s)")
else:
    st.sidebar.info("⏸️ Market closed / CSV mode")

df = None
symbol_input = "NSE:NIFTYBANK"

if source == "Upstox Live":
    try:
        token = st.secrets["UPSTOX_ACCESS_TOKEN"]
    except:
        st.error("Secrets-la UPSTOX_ACCESS_TOKEN add pannunga.")
        st.stop()

    with st.sidebar:
        symbol_input = st.selectbox("Stock / Index", list(UPSTOX_SYMBOLS.keys()))
        interval = st.selectbox("Interval", ["1minute","5minute","15minute","30minute"], index=1)
        if st.button("🔄 Refresh now"):
            st.rerun()

    try:
        with st.spinner(f"Fetching {symbol_input}..."):
            df = fetch_upstox_candles(symbol_input, interval, token)
    except Exception as e:
        st.error(f"Data fetch fail: {e}")
        st.stop()
else:
    uploaded = st.file_uploader("Upload OHLCV CSV", type=["csv"])
    if uploaded:
        df = load_csv(uploaded)
    with st.sidebar:
        symbol_input = st.text_input("Chart title", "Uploaded CSV")

if df is None:
    st.info("Sidebar-la source select pannunga illa CSV upload pannunga.")
    st.stop()

for col in ["open","high","low","close"]:
    if col not in df.columns:
        df[col] = df["close"]
if "volume" not in df.columns:
    df["volume"] = 0

result = calculate(df, length=length, smooth=smooth)
stats = summarize_trades(result)

# ---- TRADE LOG WITH PROFIT ----
trades = []
entry_row = None
for i, row in result.iterrows():
    if bool(row["buy_signal"]) and entry_row is None:
        entry_row = row
    elif bool(row["exit_signal"]) and entry_row is not None:
        trades.append({
            "Entry Time": entry_row["timestamp"],
            "Entry Price": round(float(entry_row["close"]), 2),
            "Exit Time": row["timestamp"],
            "Exit Price": round(float(row["close"]), 2),
            "Profit / Loss": round(float(row["close"]) - float(entry_row["close"]), 2),
        })
        entry_row = None
if entry_row is not None:
    trades.append({
        "Entry Time": entry_row["timestamp"],
        "Entry Price": round(float(entry_row["close"]), 2),
        "Exit Time": "OPEN",
        "Exit Price": "-",
        "Profit / Loss": round(float(result["close"].iloc[-1]) - float(entry_row["close"]), 2),
    })
trades_df = pd.DataFrame(trades)

last_close = float(result["close"].iloc[-1])
first_open = float(result["open"].iloc[0])
day_high = float(result["high"].max())
day_low = float(result["low"].min())
chg = last_close - first_open
pct = (chg / first_open * 100) if first_open != 0 else 0.0
last_pascal = float(result["pascal_value"].iloc[-1])
state = "▲ ABOVE ZERO" if last_pascal > 0 else "▼ BELOW ZERO"

st.subheader(f"{symbol_input} • {len(result)} candles • {result['timestamp'].iloc[-1].strftime('%d %b %Y')}")

a,b,c,d = st.columns(4)
a.metric("Last Price", f"{last_close:,.2f}", f"{chg:+.2f} ({pct:+.2f}%)")
b.metric("High / Low", f"{day_high:,.2f}", f"Low {day_low:,.2f}")
c.metric("Pascal Value", f"{last_pascal:.2f}", state)
if len(trades_df) > 0:
    total_pnl = trades_df["Profit / Loss"].sum()
    d.metric("Total P&L", f"{total_pnl:+,.2f}", f"{len(trades_df)} trades")
else:
    d.metric("Total P&L", "—", "0 trades")

e,f,g = st.columns(3)
e.metric("BUY signals", stats["buy_count"])
f.metric("Completed cycles", stats["completed_cycles"])
g.metric("Avg cycle", f"{stats['mean_duration']:.2f}" if stats["mean_duration"] is not None else "—")

# ---- CHART ----
fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
    row_heights=[0.5,0.15,0.35], vertical_spacing=0.06,
    subplot_titles=(f"{symbol_input} — Price","Volume","PASCAL ZERO Oscillator"))

fig.add_trace(go.Candlestick(x=result["timestamp"], open=result["open"], high=result["high"],
    low=result["low"], close=result["close"],
    increasing_line_color="#26a69a", decreasing_line_color="#ef5350", name="Price"), row=1, col=1)
fig.add_trace(go.Bar(x=result["timestamp"], y=result["volume"], marker_color="#3d5a80", name="Volume"), row=2, col=1)
fig.add_trace(go.Scatter(x=result["timestamp"], y=result["pascal_value"], name="PASCAL",
    line=dict(width=2, color="#58a6ff")), row=3, col=1)
fig.add_hline(y=0, line_color="#8b949e", line_width=1, row=3, col=1)

buys = result[result["buy_signal"]]
exits = result[result["exit_signal"]]
fig.add_trace(go.Scatter(x=buys["timestamp"], y=buys["pascal_value"], mode="markers", name="BUY",
    marker=dict(symbol="triangle-up", size=12, color="#00c853")), row=3, col=1)
fig.add_trace(go.Scatter(x=exits["timestamp"], y=exits["pascal_value"], mode="markers", name="DOWN-CROSS",
    marker=dict(symbol="triangle-down", size=11, color="#ff5252")), row=3, col=1)

fig.update_layout(height=750, template="plotly_dark", margin=dict(l=10,r=10,t=40,b=10),
    xaxis_rangeslider_visible=False, legend=dict(orientation="h", y=1.02))
st.plotly_chart(fig, use_container_width=True)

# ---- PROFIT TABLE ----
st.subheader("📋 Trade Log — Entry → Exit with P&L")
if len(trades_df) > 0:
    st.dataframe(trades_df.sort_values("Entry Time", ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("Innum trade signal varala. Interval or lookback maathi paarunga.")
