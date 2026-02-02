import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("📊 Forecasting & Staffing App")
st.write("Upload your historical data (CSV) to generate forecasts and staffing plans.")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    # الكود ده بيجرب كذا طريقة عشان يقرأ الملف مهما كان نوعه
    data = None
    encodings = ['utf-8', 'cp1256', 'latin1']
    separators = [',', ';'] # بيجرب الفاصلة العادية والمنقوطة
    
    success = False
    for enc in encodings:
        for sep in separators:
            try:
                uploaded_file.seek(0)
                data = pd.read_csv(uploaded_file, encoding=enc, sep=sep)
                # لو لقى الأعمدة المطلوبة يبقى قرأ صح
                if 'date' in data.columns and 'calls' in data.columns:
                    success = True
                    break
            except:
                continue
        if success: break

    if success and data is not None:
        st.subheader("📄 Data Preview")
        st.dataframe(data.head())

        # معالجة البيانات
        data['date'] = pd.to_datetime(data['date'])
        data = data.sort_values('date').set_index('date')

        st.subheader("📈 Forecast (Next 14 Days)")
        data['forecast_ma'] = data['calls'].rolling(7, min_periods=1).mean()
        last_val = data['forecast_ma'].iloc[-1]
        
        forecast_idx = pd.date_range(start=data.index[-1] + pd.Timedelta(days=1), periods=14)
        forecast_series = pd.Series([round(last_val)] * 14, index=forecast_idx)
        st.table(forecast_series)

        # الرسم البياني
        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(data.index, data['calls'], label='Actual')
        ax.plot(forecast_series.index, forecast_series.values, label='Forecast', linestyle='--')
        ax.legend()
        st.pyplot(fig)

        # حساب الموظفين
        calls_per_agent = 20
        required = (forecast_series / calls_per_agent).apply(lambda x: int(np.ceil(x)))
        st.subheader("👥 Required Agents")
        st.table(required)
    else:
        st.error("❌ Error: Could not read the file. Please ensure your CSV has 'date' and 'calls' columns.")
