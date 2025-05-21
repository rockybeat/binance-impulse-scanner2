
import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta

BINANCE_FUTURES_URL = "https://fapi.binance.com"

def get_futures_symbols():
    response = requests.get(f"{BINANCE_FUTURES_URL}/fapi/v1/exchangeInfo")
    data = response.json()
    symbols = [s['symbol'] for s in data['symbols'] if s['contractType'] == 'PERPETUAL']
    return symbols

def get_daily_kline(symbol, date):
    start_ts = int(datetime.strptime(date, "%Y-%m-%d").timestamp() * 1000)
    end_ts = int((datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).timestamp() * 1000)
    url = f"{BINANCE_FUTURES_URL}/fapi/v1/klines?symbol={symbol}&interval=1d&startTime={start_ts}&endTime={end_ts}"
    data = requests.get(url).json()
    if not data:
        return None
    open_price = float(data[0][1])
    close_price = float(data[0][4])
    pct_change = (close_price - open_price) / open_price * 100
    return pct_change

def get_1m_candles(symbol, date):
    start = int(datetime.strptime(date, "%Y-%m-%d").timestamp() * 1000)
    end = int((datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).timestamp() * 1000)
    all_data = []

    while start < end:
        url = f"{BINANCE_FUTURES_URL}/fapi/v1/klines?symbol={symbol}&interval=1m&startTime={start}&limit=1500"
        data = requests.get(url).json()
        if not data:
            break
        all_data += data
        start = data[-1][0] + 60_000
        time.sleep(0.2)
    return all_data

def find_impulses(candles):
    impulses = 0
    for i in range(len(candles) - 10):
        open_price = float(candles[i][1])
        max_high = max(float(c[2]) for c in candles[i:i+10])
        if (max_high - open_price) / open_price >= 0.05:
            impulses += 1
    return impulses

def run_analysis(start_date, end_date):
    symbols = get_futures_symbols()
    results = []
    date_range = pd.date_range(start=start_date, end=end_date)

    for date in date_range:
        date_str = date.strftime("%Y-%m-%d")
        for symbol in symbols:
            try:
                change = get_daily_kline(symbol, date_str)
                if change and change >= 30:
                    candles = get_1m_candles(symbol, date_str)
                    impulses = find_impulses(candles)
                    if impulses > 0:
                        results.append({
                            "Symbol": symbol,
                            "Date": date_str,
                            "Daily Growth %": round(change, 2),
                            "Impulses (>5% in <=10m)": impulses
                        })
            except Exception as e:
                st.warning(f"Error for {symbol} on {date_str}: {e}")

    return pd.DataFrame(results)

st.title("Binance Impulse Scanner")
st.markdown("Находит фьючерсные монеты Binance, которые выросли >30% за день и дали >5% импульсы за 10 минут.")

start_date = st.date_input("Дата начала", datetime(2025, 4, 1))
end_date = st.date_input("Дата окончания", datetime(2025, 5, 31))

if st.button("Запустить анализ"):
    with st.spinner("Собираем данные..."):
        df = run_analysis(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        if not df.empty:
            st.success(f"Найдено {len(df)} записей")
            st.dataframe(df)
            st.download_button("Скачать CSV", df.to_csv(index=False), file_name="impulse_report.csv")
        else:
            st.info("Нет подходящих импульсов.")
