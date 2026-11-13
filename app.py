import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="ICT SmartFlow Pro",
    layout="wide"
)

st.title("🚀 ICT SMARTFLOW PRO")
st.caption("XAUUSD | 15 Minute Trading Terminal")

@st.cache_data(ttl=60)
def get_data():
    df = yf.download(
        "GC=F",
        period="5d",
        interval="15m",
        progress=False
    )

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df.dropna()

try:
    df = get_data()

    if df.empty:
        st.error("Market data unavailable. Please refresh.")
        st.stop()

    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))
    df["RSI"] = 100 - (100 / (1 + rs))

    df["Signal"] = "WAIT"

    buy = (
        (df["EMA20"] > df["EMA50"]) &
        (df["RSI"] > 50)
    )

    sell = (
        (df["EMA20"] < df["EMA50"]) &
        (df["RSI"] < 50)
    )

    df.loc[buy, "Signal"] = "BUY"
    df.loc[sell, "Signal"] = "SELL"

    latest = df.iloc[-1]

    price = float(latest["Close"])
    signal = latest["Signal"]
    rsi = float(latest["RSI"])

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Gold Price", f"${price:,.2f}")
    c2.metric("Current Signal", signal)
    c3.metric("RSI", f"{rsi:.2f}")
    c4.metric("Timeframe", "15 Minutes")

    st.divider()

    st.subheader("📊 Live Gold Candlestick Chart")

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="XAUUSD"
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["EMA20"],
        name="EMA 20",
        line=dict(width=1.5)
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["EMA50"],
        name="EMA 50",
        line=dict(width=1.5)
    ))

    buy_points = df[df["Signal"] == "BUY"]
    sell_points = df[df["Signal"] == "SELL"]

    fig.add_trace(go.Scatter(
        x=buy_points.index,
        y=buy_points["Low"],
        mode="markers",
        name="BUY",
        marker=dict(symbol="triangle-up", size=11, color="green")
    ))

    fig.add_trace(go.Scatter(
        x=sell_points.index,
        y=sell_points["High"],
        mode="markers",
        name="SELL",
        marker=dict(symbol="triangle-down", size=11, color="red")
    ))

    fig.update_layout(
        height=650,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        legend_orientation="h"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📈 Technical Analysis")

    st.write("Latest Signal:", signal)
    st.write("EMA 20:", round(float(latest["EMA20"]), 2))
    st.write("EMA 50:", round(float(latest["EMA50"]), 2))
    st.write("RSI:", round(rsi, 2))

    st.subheader("📋 Recent Market Data")

    st.dataframe(
        df.tail(20).sort_index(ascending=False),
        use_container_width=True
    )

    st.caption(
        "Data: Yahoo Finance Gold Futures (GC=F). "
        "This is not a guaranteed real-time spot XAUUSD feed. "
        "Signals are experimental EMA/RSI indicators, not "
        "the original 29-model ICT strategy."
    )

except Exception as e:
    st.error(f"Market data error: {e}")
