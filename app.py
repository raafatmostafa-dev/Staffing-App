import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("📊 Forecasting & Staffing App")
st.write("Upload your historical data (CSV).")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    data = None
    # تجربة كل أنواع الترميز والفواصل
    for enc in ['utf-8', 'cp1256', 'latin1']:
        for sep in [',', ';', '\t']:
            try:
                uploaded_file.seek(0)
                temp_data = pd.read_csv(uploaded_file, encoding=enc, sep=sep)
                if len(temp_data.columns) >= 2:
                    data = temp_data
                    break
            except: continue
        if data is not None: break

    if data is not None:
        # تنظيف أسامي الأعمدة من أي مسافات زيادة
        data.columns = [str(c).strip().lower() for c in data.columns]
        
        st.subheader("📄 Data Preview")
        st.write("Columns found:", list(data.columns))
        st.dataframe(data.head())

        # محاولة ذكية لإيجاد عمود التاريخ وعمود الأرقام
        date_col = None
        val_col = None
        
        for col in data.columns:
            if 'date' in col or 'time' in col or 'تاريخ' in col:
                date_col = col
            elif data[col].dtype in [np.float64, np.int64] or 'call' in col or 'مكالمات' in col:
                val_col = col

        if date_col and val_col:
            try:
                data[date_col] = pd.to_datetime(data[date_col])
                data = data.sort_values(date_col).set_index(date_col)

                st.subheader("📈 Forecast (Next 14 Days)")
                # حساب التوقعات
                ma_val = data[val_col].rolling(7, min_periods=1).mean().iloc[-1]
                forecast_idx = pd.date_range(start=data.index[-1] + pd.Timedelta(days=1), periods=14)
                forecast_series = pd.Series([round(ma_val)] * 14, index=forecast_idx)
                st.table(forecast_series)

                # الرسم البياني
                fig, ax = plt.subplots(figsize=(10,5))
                ax.plot(data.index, data[val_col], label='Actual')
                ax.plot(forecast_series.index, forecast_series.values, label='Forecast', linestyle='--')
                ax.legend()
                st.pyplot(fig)

                # حساب الموظفين
                agents = (forecast_series / 20).apply(lambda x: int(np.ceil(x)))
                st.subheader("👥 Required Agents")
                st.table(agents)
            except Exception as e:
                st.error(f"Error processing data: {e}")
        else:
            st.error("❌ Could not find 'date' and 'calls' columns. Please rename them in your CSV.")
    else:
        st.error("❌ Could not read the file at all.")
