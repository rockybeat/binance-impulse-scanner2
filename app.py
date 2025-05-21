import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

BINANCE_FUTURES_URL = "https://fapi.binance.com"

def get_futures_symbols():
    # Фиксированный список известных пампов
    return ["MOODENGUSDT", "PARTIUSDT", "DEGENUSDT", "PNUTUSDT", "KATOUUSDT", "FAIRUSDT"]

def get_daily_kline(symbol, date):
    start_ts = int(datetime.strptime(date, "%Y-%m-%d").timestamp() * 1000)
    end_ts = int((datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).timestamp() * 1000)
    url = f"{BINANCE_FUTURES_URL}/fapi/v1/klines?symbol={symbol}&interval=1d&startTime={start_ts}&endTime={end_ts}"
    
    st.write(f"📡 Запрос дневных данных: {symbol} ({date})")
    try:
        response = requests.get(url)
        data = response.json()
        st.write(f"🔁 Ответ: {data}")
        
        if not data or isinstance(data, dict):
            return None
        
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        pct_change = (close_price - open_price) / open_price * 100
        return pct_change
    except Exception as e:
        st.error(f"❌ Ошибка при получении свечей для {symbol} — {e}")
        return None

def run_analysis(start_date, end_date):
    symbols = get_futures_symbols()
    st.write(f"🧪 Анализируем {len(symbols)} монет с {start_date} по {end_date}")
    
    results = []
    date_range = pd.date_range(start=start_date, end=end_date)

    for date in date_range:
        date_str = date.strftime("%Y-%m-%d")
        st.write(f"📅 Проверка даты: {date_str}")
        for symbol in symbols:
            change = get_daily_kline(symbol, date_str)
            if change is not None:
                st.write(f"➡️ {symbol} дал {change:.2f}%")
                results.append({
                    "Symbol": symbol,
                    "Date": date_str,
                    "Daily Growth %": round(change, 2)
                })
            else:
                results.append({
                    "Symbol": symbol,
                    "Date": date_str,
                    "Daily Growth %": "нет данных"
                })
    return pd.DataFrame(results)

# --- Streamlit UI ---
st.title("🧪 Binance Impulse Debugger (FIXED LIST)")
st.markdown("Диагностика: проверка фиксированных монет на дневной рост и корректность API Binance.")

start_date = st.date_input("Дата начала", datetime(2025, 5, 5))
end_date = st.date_input("Дата окончания", datetime(2025, 5, 7))

if st.button("🚀 Запустить диагностику"):
    with st.spinner("Получаем данные с Binance..."):
        df = run_analysis(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        if not df.empty:
            st.success(f"✅ Найдено {len(df)} записей.")
            st.dataframe(df)
            st.download_button("📥 Скачать как CSV", df.to_csv(index=False), file_name="binance_debug.csv")
        else:
            st.warning("⚠️ Нет данных по выбранным монетам.")
