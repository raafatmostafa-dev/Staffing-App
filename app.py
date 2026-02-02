import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_option('deprecation.showPyplotGlobalUse', False)

st.title("📊 Forecasting & Staffing App")
st.write("Upload your historical data (CSV) to generate forecasts and staffing plans.")

# رفع ملف CSV
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    # محاولة قراءة الملف بالترميز الصحيح
    try:
        data = pd.read_csv(uploaded_file)
    except UnicodeDecodeError:
        data = pd.read_csv(uploaded_file, encoding='cp1256')  # للملفات العربية

    st.subheader("📄 Data Preview")
    st.dataframe(data.head())

    # التأكد من وجود الأعمدة الأساسية
    if 'date' in data.columns and 'calls' in data.columns:
        data['date'] = pd.to_datetime(data['date'])
        data = data.set_index('date')

        st.subheader("📈 Forecast (Next 14 Days)")

        # Forecast بسيط: Moving Average
        data['forecast'] = data['calls'].rolling(7, min_periods=1).mean()
        last_forecast = data['forecast'].iloc[-1]
        forecast_values = [round(last_forecast)] * 14  # forecast 14 يوم
        forecast_index = pd.date_range(start=data.index[-1] + pd.Timedelta(days=1), periods=14)
        forecast_series = pd.Series(forecast_values, index=forecast_index)

        st.table(forecast_series)

        # رسم البيانات
        plt.figure(figsize=(10,5))
        plt.plot(data.index, data['calls'], label='Actual Calls')
        plt.plot(forecast_series.index, forecast_series.values, label='Forecast', linestyle='--')
        plt.xlabel('Date')
        plt.ylabel('Calls')
        plt.legend()
        plt.grid(True)
        st.pyplot()

        # حساب عدد agents المطلوب (مثال: كل agent يعالج 20 call/day)
        calls_per_agent = 20
        required_agents = (forecast_series / calls_per_agent).apply(lambda x: round(x))
        st.subheader("👥 Required Agents per Day")
        st.table(required_agents)

    else:
        st.error("CSV must have columns: 'date' and 'calls'.")