import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(
    page_title="ICT SmartFlow Pro",
    layout="wide"
)

st.title("ICT SmartFlow Pro Trading Dashboard")

st.success("Trading Dashboard is Running!")

st.sidebar.title("Navigation")

page = st.sidebar.selectbox(
    "Select Page",
    ["Dashboard", "Market Data", "ICT Signals",
     "Risk Calculator", "Backtesting", "Model Reports"]
)

st.header(page)
st.write("Welcome to ICT SmartFlow Pro")
