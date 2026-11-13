import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(
    page_title="ICT SmartFlow Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp {background:#080d18;color:#e5e7eb;}
[data-testid="stMetric"] {
    background:#111a2b;
    border:1px solid #263650;
    padding:15px;
    border-radius:12px;
}
h1 {color:#e8f1ff;}
.block-container {padding-top:1.5rem;}
</style>
""", unsafe_allow_html=True)

st.title("📈 ICT SMARTFLOW PRO")
st.caption("Professional Gold Market Analysis Dashboard | 15 Minute Timeframe")

with st.sidebar:
    st.header("⚙️ Dashboard Settings")
    symbol = st.selectbox("Market", ["GC=F"])
    timeframe = st.selectbox("Timeframe", ["15m", "30m", "1h"])
    refresh = st.button("🔄 Refresh Market Data", use_container_width=True)
    st.divider()
    st.caption("Data provider: Yahoo Finance")
    st.caption("Instrument: Gold Futures (GC=F)")
    st.caption("Signals: Experimental EMA + RSI")

@st.cache_data(ttl=60)
def load_data(symbol, timeframe):
    data = yf.download(
        symbol,
        period="5d",
        interval=timeframe,
        auto_adjust=False,
        progress=False
    )

    if data.empty:
        return pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.loc[:, ~data.columns.duplicated()]
    data = data.dropna(subset=["Open", "High", "Low", "Close"]).copy()

    data["EMA20"] = data["Close"].ewm(span=20, adjust=False).mean()
    data["EMA50"] = data["Close"].ewm(span=50, adjust=False).mean()

    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    data["RSI"] = 100 - (100 / (1 + rs))
    data["RSI"] = data["RSI"].fillna(50)

    data["Signal"] = "WAIT"
    buy = (data["EMA20"] > data["EMA50"]) & (data["RSI"] > 50)
    sell = (data["EMA20"] < data["EMA50"]) & (data["RSI"] < 50)

    data.loc[buy, "Signal"] = "BUY"
    data.loc[sell, "Signal"] = "SELL"

    return data

if refresh:
    st.cache_data.clear()

try:
    df = load_data(symbol, timeframe)

    if df.empty:
        st.error("Market data available nahi. Refresh karke dobara try karein.")
        st.stop()

    last = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else last

    signal = last["Signal"]
    trend = "BULLISH" if last["EMA20"] > last["EMA50"] else "BEARISH"
    change = last["Close"] - previous["Close"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("GOLD PRICE", f"{last['Close']:,.2f}", f"{change:+.2f}")
    c2.metric("MARKET TREND", trend)
    c3.metric("RSI (14)", f"{last['RSI']:.2f}")
    c4.metric("CURRENT SIGNAL", signal)

    st.divider()

    st.subheader("🕯️ Advanced Candlestick Chart")
    st.caption("Zoom: mouse wheel | Pan: drag | Hover: candle details")

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.035,
        row_heights=[0.62, 0.18, 0.20],
        subplot_titles=("PRICE ACTION + EMA", "TRADING VOLUME", "RSI (14)")
    )

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Candles",
        increasing_line_color="#00d68f",
        decreasing_line_color="#ff496c",
        increasing_fillcolor="#00d68f",
        decreasing_fillcolor="#ff496c",
        whiskerwidth=0.7
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=df["EMA20"],
        name="EMA 20",
        line=dict(color="#ffd166", width=2)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=df["EMA50"],
        name="EMA 50",
        line=dict(color="#42a5ff", width=2)
    ), row=1, col=1)

    buy_points = df[df["Signal"] == "BUY"]
    sell_points = df[df["Signal"] == "SELL"]

    fig.add_trace(go.Scatter(
        x=buy_points.index,
        y=buy_points["Low"] * 0.999,
        mode="markers",
        name="BUY",
        marker=dict(symbol="triangle-up", size=12, color="#00ff99")
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=sell_points.index,
        y=sell_points["High"] * 1.001,
        mode="markers",
        name="SELL",
        marker=dict(symbol="triangle-down", size=12, color="#ff496c")
    ), row=1, col=1)

    volume_colors = np.where(
        df["Close"] >= df["Open"], "#00d68f", "#ff496c"
    )

    fig.add_trace(go.Bar(
        x=df.index,
        y=df["Volume"],
        name="Volume",
        marker_color=volume_colors
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI"],
        name="RSI",
        line=dict(color="#c792ea", width=2)
    ), row=3, col=1)

    fig.add_hline(y=70, line_dash="dash", line_color="#ff496c", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#00d68f", row=3, col=1)

    fig.update_layout(
        template="plotly_dark",
        height=850,
        paper_bgcolor="#080d18",
        plot_bgcolor="#0d1626",
        font=dict(color="#e5e7eb"),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        dragmode="pan",
        legend=dict(orientation="h", y=1.03, x=0),
        margin=dict(l=20, r=20, t=65, b=20)
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#1d2a40",
        showspikes=True,
        spikemode="across"
    )
    fig.update_yaxes(showgrid=True, gridcolor="#1d2a40")

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displaylogo": False,
            "responsive": True
        }
    )

    st.divider()
    st.subheader("📊 Market Analysis")

    a, b, c = st.columns(3)
    a.metric("EMA 20", f"{last['EMA20']:,.2f}")
    b.metric("EMA 50", f"{last['EMA50']:,.2f}")
    c.metric("RSI STATUS",
             "Overbought" if last["RSI"] >= 70
             else "Oversold" if last["RSI"] <= 30
             else "Neutral")

    st.subheader("📋 Latest Market Data")
    display = df[["Open", "High", "Low", "Close", "Volume",
                  "EMA20", "EMA50", "RSI", "Signal"]].tail(20).sort_index(ascending=False)

    st.dataframe(display, use_container_width=True)

    st.caption(
        f"Last data timestamp: {df.index[-1]} | "
        f"Data retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    st.info(
        "Educational prototype: signals are experimental EMA/RSI rules, "
        "not the complete ICT 29-model strategy. Yahoo Finance GC=F is "
        "Gold Futures data and may be delayed; it is not guaranteed live spot XAUUSD."
    )

except Exception as e:
    st.error(f"App error: {e}")
    st.info("Please refresh the app. If the issue continues, share a screenshot.")
