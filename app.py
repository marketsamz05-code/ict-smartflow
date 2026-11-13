import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="NY Gold Live Chart",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #080d18;
}
h1 {
    color: #ffffff;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

st.title("NY GOLD LIVE CHART")
st.caption("XAUUSD | TradingView Advanced Chart")

chart_html = """
<div style="height:700px;width:100%">
    <div class="tradingview-widget-container"
         style="height:100%;width:100%">

        <div class="tradingview-widget-container__widget"
             style="height:100%;width:100%">
        </div>

        <script
        type="text/javascript"
        src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js"
        async>
        {
            "autosize": true,
            "symbol": "OANDA:XAUUSD",
            "interval": "5",
            "timezone": "Asia/Karachi",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "allow_symbol_change": true,
            "calendar": false,
            "hide_side_toolbar": false,
            "hide_top_toolbar": false,
            "hide_legend": false,
            "hide_volume": false,
            "save_image": true,
            "support_host": "https://www.tradingview.com"
        }
        </script>
    </div>
</div>
"""

components.html(
    chart_html,
    height=720,
    scrolling=False
)


