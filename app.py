import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("📊 Forecasting & Staffing App")
st.write("Upload your file (CSV or Excel).")

# بنخلي الأبلكيشن يقبل CSV و Excel كمان عشان نريحك
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])

if uploaded_file:
    data = None
    try:
        # لو الملف إكسيل
        if uploaded_file.name.endswith('.xlsx'):
            data = pd.read_excel(uploaded_file)
        else:
            # لو CSV بنجرب كذا ترميز
            for enc in ['utf-8', 'cp1256', 'latin1']:
                try:
                    uploaded_file.seek(0)
                    data = pd.read_csv(uploaded_file, encoding=enc)
                    if len(data.columns) > 1: break
                except: continue
    except Exception as e:
        st.error(f"Error reading file: {e}")

    if data is not None:
        # تنظيف أسامي الأعمدة
        data.columns = [str(c).strip().lower() for c in data.columns]
        st.subheader("📄 Data Preview")
        st.write("Columns found:", list(data.columns))
        st.dataframe(data.head())

        # البحث عن الأعمدة (تاريخ ومكالمات)
        date_col = next((c for c in data.columns if 'date' in c or 'تاريخ' in c), None)
        val_col = next((c for c in data.columns if 'call' in c or 'مكالمات' in c or 'value' in c), None)

        if date_col and val_col:
            data[date_col] = pd.to_datetime(data[date_col])
            data = data.sort_values(date_col).set_index(date_col)
            
            # حساب الفوركاست (متوسط 7 أيام)
            ma_val = data[val_col].tail(7).mean()
            forecast_idx = pd.date_range(start=data.index[-1] + pd.Timedelta(days=1), periods=14)
            forecast_series = pd.Series([round(ma_val)] * 14, index=forecast_idx)
            
            st.subheader("📈 Staffing Forecast")
            fig, ax = plt.subplots(figsize=(10,5))
            ax.plot(data.index, data[val_col], label='Actual')
            ax.plot(forecast_series.index, forecast_series.values, '--', label='Forecast')
            ax.legend(); st.pyplot(fig)

            # حساب الموظفين (كل موظف 20 مكالمة)
            st.subheader("👥 Required Agents (Next 14 Days)")
            agents = (forecast_series / 20).apply(np.ceil)
            st.table(agents)
        else:
            st.error("❌ Please make sure the file has columns named 'date' and 'calls'.")
