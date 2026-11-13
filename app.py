import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="ICT SmartFlow Pro",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
.stApp {background-color: #080d18;}
h1, h2, h3, p, label {color: #e8edf7;}
[data-testid="stMetric"] {
    background: #111b2d;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #26364d;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def get_data(symbol):
    intraday = yf.download(
        symbol,
        period="60d",
        interval="15m",
        auto_adjust=True,
        progress=False
    )

    daily = yf.download(
        symbol,
        period="1y",
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    def clean(df):
        if df is None or df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.columns = [str(c).lower() for c in df.columns]
        return df.dropna()

    return clean(intraday), clean(daily)


def calculate_daily_bias(daily):
    daily = daily.copy()

    daily["ema20"] = daily["close"].ewm(
        span=20, adjust=False
    ).mean()

    daily["ema50"] = daily["close"].ewm(
        span=50, adjust=False
    ).mean()

    daily["ema20_slope"] = daily["ema20"].diff(3)

    last = daily.iloc[-1]

    if (
        last["close"] > last["ema20"]
        and last["ema20"] > last["ema50"]
        and last["ema20_slope"] > 0
    ):
        return "BULLISH"

    if (
        last["close"] < last["ema20"]
        and last["ema20"] < last["ema50"]
        and last["ema20_slope"] < 0
    ):
        return "BEARISH"

    return "NEUTRAL"


def generate_signals(df, bias, pip_size, sl_pips):
    df = df.copy()

    df["ema20"] = df["close"].ewm(
        span=20, adjust=False
    ).mean()

    df["ema50"] = df["close"].ewm(
        span=50, adjust=False
    ).mean()

    # Previous liquidity levels
    df["previous_high"] = df["high"].rolling(20).max().shift(1)
    df["previous_low"] = df["low"].rolling(20).min().shift(1)

    # Market structure levels
    df["structure_high"] = df["high"].rolling(5).max().shift(1)
    df["structure_low"] = df["low"].rolling(5).min().shift(1)

    # Fair Value Gap
    df["bullish_fvg"] = (
        df["low"] > df["high"].shift(2)
    )

    df["bearish_fvg"] = (
        df["high"] < df["low"].shift(2)
    )

    # Liquidity sweep
    df["sellside_sweep"] = (
        (df["low"] < df["previous_low"])
        & (df["close"] > df["previous_low"])
    )

    df["buyside_sweep"] = (
        (df["high"] > df["previous_high"])
        & (df["close"] < df["previous_high"])
    )

    # Market Structure Shift
    df["bullish_mss"] = (
        df["close"] > df["structure_high"]
    )

    df["bearish_mss"] = (
        df["close"] < df["structure_low"]
    )

    df["signal"] = ""

    buy = (
        (bias == "BULLISH")
        & df["sellside_sweep"]
        & df["bullish_mss"]
        & df["bullish_fvg"]
        & (df["ema20"] > df["ema50"])
    )

    sell = (
        (bias == "BEARISH")
        & df["buyside_sweep"]
        & df["bearish_mss"]
        & df["bearish_fvg"]
        & (df["ema20"] < df["ema50"])
    )

    df.loc[buy, "signal"] = "BUY"
    df.loc[sell, "signal"] = "SELL"

    df["entry"] = np.nan
    df["sl"] = np.nan
    df["tp"] = np.nan

    distance = sl_pips * pip_size

    buy_mask = df["signal"] == "BUY"
    sell_mask = df["signal"] == "SELL"

    df.loc[buy_mask, "entry"] = df.loc[buy_mask, "close"]
    df.loc[buy_mask, "sl"] = df.loc[buy_mask, "close"] - distance
    df.loc[buy_mask, "tp"] = df.loc[buy_mask, "close"] + (distance * 2)

    df.loc[sell_mask, "entry"] = df.loc[sell_mask, "close"]
    df.loc[sell_mask, "sl"] = df.loc[sell_mask, "close"] + distance
    df.loc[sell_mask, "tp"] = df.loc[sell_mask, "close"] - (distance * 2)

    return df


st.title("📈 ICT SMARTFLOW PRO")
st.caption("Daily Market Direction | Liquidity | MSS | FVG | Risk Management")

with st.sidebar:
    st.header("Trading Settings")

    symbol = st.text_input(
        "Trading Symbol",
        value="EURUSD=X"
    )

    pip_size = st.number_input(
        "Pip Size",
        min_value=0.00001,
        value=0.0001,
        step=0.00001,
        format="%.5f"
    )

    sl_pips = st.slider(
        "Stop Loss (Pips)",
        40, 50, 45
    )

    st.metric("Risk Reward", "1 : 2")
    st.metric("Take Profit", f"{sl_pips * 2} Pips")

    refresh = st.button("🔄 Refresh Market Data", use_container_width=True)

if refresh:
    st.cache_data.clear()

try:
    with st.spinner("Loading live market data..."):
        intraday, daily = get_data(symbol.strip().upper())

    if intraday.empty or daily.empty:
        st.error("Market data unavailable. Check symbol and try again.")
        st.stop()

    bias = calculate_daily_bias(daily)

    result = generate_signals(
        intraday,
        bias,
        pip_size,
        sl_pips
    )

    # Ignore the latest potentially incomplete candle
    if len(result) > 1:
        result = result.iloc[:-1].copy()

    latest = result.iloc[-1]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("DAILY DIRECTION", bias)
    c2.metric("TIMEFRAME", "15 MIN")
    c3.metric("STOP LOSS", f"{sl_pips} Pips")
    c4.metric("TAKE PROFIT", f"{sl_pips * 2} Pips")

    st.divider()

    if latest["signal"] == "BUY":
        st.success("BUY SIGNAL CONFIRMED")

    elif latest["signal"] == "SELL":
        st.error("SELL SIGNAL CONFIRMED")

    elif bias == "NEUTRAL":
        st.warning("NO TRADE — DAILY DIRECTION UNCLEAR")

    else:
        st.info("WAITING FOR ICT SETUP CONFIRMATION")

    signals = result[result["signal"] != ""]

    if not signals.empty:
        last_signal = signals.iloc[-1]

        st.subheader("Latest Confirmed Setup")

        a, b, c, d = st.columns(4)

        a.metric("SIGNAL", last_signal["signal"])
        b.metric("ENTRY", f"{last_signal['entry']:.5f}")
        c.metric("STOP LOSS", f"{last_signal['sl']:.5f}")
        d.metric("TAKE PROFIT", f"{last_signal['tp']:.5f}")

        st.caption(
            f"Signal candle: {last_signal.name}"
        )

    st.subheader("Live Market Chart")

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=result.index,
        open=result["open"],
        high=result["high"],
        low=result["low"],
        close=result["close"],
        name="Price"
    ))

    fig.add_trace(go.Scatter(
        x=result.index,
        y=result["ema20"],
        name="EMA 20",
        line=dict(color="orange", width=1)
    ))

    fig.add_trace(go.Scatter(
        x=result.index,
        y=result["ema50"],
        name="EMA 50",
        line=dict(color="cyan", width=1)
    ))

    buys = result[result["signal"] == "BUY"]
    sells = result[result["signal"] == "SELL"]

    fig.add_trace(go.Scatter(
        x=buys.index,
        y=buys["low"],
        mode="markers+text",
        name="BUY",
        text=["BUY"] * len(buys),
        textposition="bottom center",
        marker=dict(
            color="#00e676",
            size=12,
            symbol="triangle-up"
        )
    ))

    fig.add_trace(go.Scatter(
        x=sells.index,
        y=sells["high"],
        mode="markers+text",
        name="SELL",
        text=["SELL"] * len(sells),
        textposition="top center",
        marker=dict(
            color="#ff1744",
            size=12,
            symbol="triangle-down"
        )
    ))

    fig.update_layout(
        height=700,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        margin=dict(l=10, r=10, t=30, b=10)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent ICT Signals")

    if not signals.empty:
        history = signals.tail(10)[
            ["signal", "entry", "sl", "tp"]
        ].sort_index(ascending=False)

        st.dataframe(
            history,
            use_container_width=True
        )
    else:
        st.info("No confirmed setups found yet.")

    st.caption(
        "Data provider: Yahoo Finance | "
        "15-minute data may be delayed. "
        "Signals are rule-based and require backtesting."
    )

except Exception as e:
    st.error(f"System Error: {e}")
    st.info("Check your symbol, internet connection and market data.")
