import streamlit as st
import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="HK Scanner", layout="wide")
st.title("📈 HK 30MA Breakout Scanner")

# Settings
col1, col2, col3 = st.columns(3)
ma_period = col1.number_input("MA Period", value=30, min_value=5)
threshold = col2.number_input("Threshold %", value=0.5, step=0.1)
vol_ratio = col3.number_input("Min Vol Ratio", value=1.5, step=0.1)

HK_STOCKS = ["0700.HK", "9988.HK", "0005.HK", "1299.HK", "0941.HK", 
             "2318.HK", "0388.HK", "1810.HK", "9618.HK", "3690.HK",
             "0001.HK", "0016.HK", "0027.HK", "0066.HK", "0175.HK"]

@st.cache_data(ttl=300)  # Cache for 5 minutes
def download_data(symbols):
    return yf.download(symbols, period="60d", threads=True, group_by='ticker')

if st.button("🔍 Scan Now", type="primary"):
    with st.spinner("Downloading data..."):
        data = download_data(HK_STOCKS)
    
    results = []
    for symbol in HK_STOCKS:
        try:
            df = data[symbol].copy()
            if len(df) < ma_period:
                continue
            
            df['MA30'] = df['Close'].rolling(ma_period).mean()
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            distance_pct = ((latest['Close'] - latest['MA30']) / latest['MA30']) * 100
            vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
            current_vol_ratio = latest['Volume'] / vol_avg if vol_avg > 0 else 0
            
            signal = None
            if prev['Close'] <= prev['MA30'] and latest['Close'] > latest['MA30']:
                if distance_pct >= threshold and current_vol_ratio >= vol_ratio:
                    signal = "🟢 BULLISH"
            elif prev['Close'] >= prev['MA30'] and latest['Close'] < latest['MA30']:
                if distance_pct <= -threshold and current_vol_ratio >= vol_ratio:
                    signal = "🔴 BEARISH"
            
            if signal:
                results.append({
                    'Symbol': symbol,
                    'Price': f"${latest['Close']:.2f}",
                    'MA30': f"${latest['MA30']:.2f}",
                    'Distance%': f"{distance_pct:+.2f}%",
                    'Signal': signal,
                    'Vol Ratio': f"{current_vol_ratio:.2f}x"
                })
        except Exception as e:
            pass
    
    if results:
        st.success(f"Found {len(results)} signals!")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.info("No breakout signals found today")

st.caption("Data from Yahoo Finance • Refresh page to scan again")
