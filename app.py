import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("📊 Forecasting & Staffing App")
st.write("Upload your historical data (CSV) to generate forecasts and staffing plans.")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    try:
        data = pd.read_csv(uploaded_file)
    except UnicodeDecodeError:
        data = pd.read_csv(uploaded_file, encoding='cp1256')

    st.subheader("📄 Data Preview")
    st.dataframe(data.head())

    if 'date' in data.columns and 'calls' in data.columns:
        data['date'] = pd.to_datetime(data['date'])
        data = data.set_index('date')

        st.subheader("📈 Forecast (Next 14 Days)")
        data['forecast_ma'] = data['calls'].rolling(7, min_periods=1).mean()
        last_forecast = data['forecast_ma'].iloc[-1]
        
        forecast_index = pd.date_range(start=data.index[-1] + pd.Timedelta(days=1), periods=14)
        forecast_series = pd.Series([round(last_forecast)] * 14, index=forecast_index)
        st.table(forecast_series)

        # الطريقة الجديدة للرسم عشان الأيرور ما يتكررش
        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(data.index, data['calls'], label='Actual Calls')
        ax.plot(forecast_series.index, forecast_series.values, label='Forecast', linestyle='--')
        ax.set_xlabel('Date')
        ax.set_ylabel('Calls')
        ax.legend()
        ax.grid(True)
        st.pyplot(fig) # هنا بعتنا fig عشان نتجنب الأيرور

        calls_per_agent = 20
        required_agents = (forecast_series / calls_per_agent).apply(lambda x: round(x))
        st.subheader("👥 Required Agents per Day")
        st.table(required_agents)
    else:
        st.error("CSV must have columns: 'date' and 'calls'.")
