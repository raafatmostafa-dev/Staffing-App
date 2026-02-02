import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("📊 Forecasting & Staffing App")
st.write("Upload your historical data (CSV) to generate forecasts and staffing plans.")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    try:
        # بنحاول نقرأ بـ UTF-8
        data = pd.read_csv(uploaded_file)
    except Exception:
        # لو فشل، بنرجع مؤشر الملف للبداية (0) عشان ميقراش ملف فاضي
        uploaded_file.seek(0)
        # بنجرب الترميز العربي
        data = pd.read_csv(uploaded_file, encoding='cp1256')

    st.subheader("📄 Data Preview")
    st.dataframe(data.head())

    # التأكد إن الأعمدة أساميها صح (لازم date و calls)
    if 'date' in data.columns and 'calls' in data.columns:
        data['date'] = pd.to_datetime(data['date'])
        data = data.sort_values('date') # ترتيب التواريخ
        data = data.set_index('date')

        st.subheader("📈 Forecast (Next 14 Days)")
        # حساب المتوسط المتحرك لآخر 7 أيام
        data['forecast_ma'] = data['calls'].rolling(7, min_periods=1).mean()
        last_forecast = data['forecast_ma'].iloc[-1]
        
        # توقع الـ 14 يوم الجايين
        forecast_index = pd.date_range(start=data.index[-1] + pd.Timedelta(days=1), periods=14)
        forecast_series = pd.Series([round(last_forecast)] * 14, index=forecast_index)
        st.table(forecast_series)

        # الرسم البياني
        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(data.index, data['calls'], label='Actual Calls', color='blue')
        ax.plot(forecast_series.index, forecast_series.values, label='Forecast', linestyle='--', color='orange')
        ax.set_title("Actual vs Forecasted Calls")
        ax.legend()
        st.pyplot(fig)

        # حساب عدد الموظفين (بفرض إن الموظف بيشيل 20 مكالمة)
        calls_per_agent = 20
        required_agents = (forecast_series / calls_per_agent).apply(lambda x: int(np.ceil(x)))
        st.subheader("👥 Required Agents per Day")
        st.table(required_agents)
    else:
        st.error("Make sure your CSV has 'date' and 'calls' columns.")
