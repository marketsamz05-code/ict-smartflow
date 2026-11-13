import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="ICT SmartFlow Pro",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
.stApp {background:#090e17;color:#e5e7eb;}
.block-container {padding-top:1.2rem;max-width:1600px;}
[data-testid="stMetric"] {
    background:#111a29;
    border:1px solid #26364d;
    padding:14px;
    border-radius:10px;
}
h1 {color:#eaf2ff;}
</style>
""", unsafe_allow_html=True)

st.title("ICT SMARTFLOW PRO")
st.caption("PROFESSIONAL MARKET ANALYSIS TERMINAL")

with st.sidebar:
    st.header("MARKET SETTINGS")
    symbol = st.selectbox("Instrument", ["GC=F"])
    interval = st.selectbox("Timeframe", ["15m", "30m", "1h"])
    if st.button("🔄 Refresh Chart", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

@st.cache_data(ttl=60)
def get_market_data(symbol, interval):
    df = yf.download(
        symbol,
        period="5d",
        interval=interval,
        progress=False,
        auto_adjust=False
    )

    if df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.loc[:, ~df.columns.duplicated()].copy()
    df = df.dropna(subset=["Open", "High", "Low", "Close"])

    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)

    df["RSI"] = (100 - 100 / (1 + rs)).fillna(50)

    df["Signal"] = "WAIT"
    df.loc[(df["EMA20"] > df["EMA50"]) & (df["RSI"] > 50), "Signal"] = "BUY"
    df.loc[(df["EMA20"] < df["EMA50"]) & (df["RSI"] < 50), "Signal"] = "SELL"

    return df

try:
    df = get_market_data(symbol, interval)

    if df.empty:
        st.error("Market data unavailable. Please refresh.")
        st.stop()

    last = df.iloc[-1]
    change = last["Close"] - df.iloc[-2]["Close"] if len(df) > 1 else 0

    trend = "BULLISH" if last["EMA20"] > last["EMA50"] else "BEARISH"
    signal = last["Signal"]

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("GOLD PRICE", f"{last['Close']:,.2f}", f"{change:+.2f}")
    p2.metric("MARKET TREND", trend)
    p3.metric("RSI", f"{last['RSI']:.2f}")
    p4.metric("LATEST SIGNAL", signal)

    st.divider()

    st.subheader("GOLD PRICE ACTION")
    st.caption("Clean TradingView-style chart | Zoom, pan and crosshair enabled")

    chart = go.Figure()

    chart.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Price",
        increasing=dict(
            line=dict(color="#26a69a", width=1),
            fillcolor="#26a69a"
        ),
        decreasing=dict(
            line=dict(color="#ef5350", width=1),
            fillcolor="#ef5350"
        ),
        whiskerwidth=0.5
    ))

    chart.add_trace(go.Scatter(
        x=df.index, y=df["EMA20"],
        name="EMA 20",
        line=dict(color="#ffca28", width=1.5)
    ))

    chart.add_trace(go.Scatter(
        x=df.index, y=df["EMA50"],
        name="EMA 50",
        line=dict(color="#42a5f5", width=1.5)
    ))

    # Show only the last 3 signal labels. No triangles or arrows.
    signals = df[df["Signal"].isin(["BUY", "SELL"])].tail(3)

    for signal_name, color in [("BUY", "#00d68f"), ("SELL", "#ff5964")]:
        selected = signals[signals["Signal"] == signal_name]
        if not selected.empty:
            chart.add_trace(go.Scatter(
                x=selected.index,
                y=selected["Close"],
                mode="text",
                text=[signal_name] * len(selected),
                textposition="top center" if signal_name == "SELL" else "bottom center",
                textfont=dict(color=color, size=11, family="Arial Black"),
                name=signal_name
            ))

    chart.update_layout(
        template="plotly_dark",
        height=680,
        paper_bgcolor="#090e17",
        plot_bgcolor="#090e17",
        margin=dict(l=10, r=55, t=35, b=10),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        dragmode="pan",
        legend=dict(
            orientation="h",
            y=1.04,
            x=0
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#1c2736",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor"
        ),
        yaxis=dict(
            side="right",
            showgrid=True,
            gridcolor="#1c2736",
            fixedrange=False
        )
    )

    st.plotly_chart(
        chart,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displaylogo": False,
            "responsive": True
        }
    )

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("📊 RSI INDICATOR")
        rsi_chart = go.Figure()
        rsi_chart.add_trace(go.Scatter(
            x=df.index,
            y=df["RSI"],
            name="RSI 14",
            line=dict(color="#b388ff", width=2)
        ))
        rsi_chart.add_hline(y=70, line_dash="dash", line_color="#ef5350")
        rsi_chart.add_hline(y=30, line_dash="dash", line_color="#26a69a")
        rsi_chart.update_layout(
            template="plotly_dark",
            height=250,
            paper_bgcolor="#090e17",
            plot_bgcolor="#090e17",
            margin=dict(l=5, r=5, t=20, b=5),
            yaxis=dict(range=[0, 100])
        )
        st.plotly_chart(rsi_chart, use_container_width=True)

    with right:
        st.subheader("📊 VOLUME")
        volume_colors = [
            "#26a69a" if c >= o else "#ef5350"
            for c, o in zip(df["Close"], df["Open"])
        ]
        vol_chart = go.Figure(go.Bar(
            x=df.index,
            y=df["Volume"],
            marker_color=volume_colors,
            name="Volume"
        ))
        vol_chart.update_layout(
            template="plotly_dark",
            height=250,
            paper_bgcolor="#090e17",
            plot_bgcolor="#090e17",
            margin=dict(l=5, r=5, t=20, b=5)
        )
        st.plotly_chart(vol_chart, use_container_width=True)

    st.subheader("LATEST MARKET SIGNALS")

    recent = df[["Close", "EMA20", "EMA50", "RSI", "Signal"]].tail(10)
    st.dataframe(recent.sort_index(ascending=False), use_container_width=True)

    st.caption(
        "Data: Yahoo Finance Gold Futures (GC=F). "
        "Signals use experimental EMA/RSI rules, not the complete ICT model. "
        "Data may be delayed and is not guaranteed live spot XAUUSD."
    )

except Exception as e:
    st.error(f"Market dashboard error: {e}")
    st.info("Refresh the app and check the data connection.")
