import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("📊 Forecasting & Staffing App")
st.write("Upload your file (CSV or Excel).")

uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.xlsx'):
            data = pd.read_excel(uploaded_file)
        else:
            data = pd.read_csv(uploaded_file, encoding='cp1256')
        
        # تنظيف أسامي الأعمدة
        data.columns = [str(c).strip().lower() for c in data.columns]
        st.subheader("📄 Data Preview")
        st.dataframe(data.head())

        # البحث عن الأعمدة (بما إن عندك week و calls)
        col1 = data.columns[0] # أول عمود (الأسابيع)
        col2 = data.columns[1] # ثاني عمود (المكالمات)

        st.subheader("📈 Forecast (Next 4 Periods)")
        
        # حساب الفوركاست بناءً على آخر القيم
        avg_calls = data[col2].tail(4).mean()
        
        # إنشاء أسابيع جديدة للمستقبل
        last_week_num = len(data)
        future_weeks = [f"Week {i}" for i in range(last_week_num + 1, last_week_num + 5)]
        forecast_values = [round(avg_calls)] * 4
        
        forecast_df = pd.DataFrame({col1: future_weeks, 'Forecasted Calls': forecast_values})
        st.table(forecast_df)

        # الرسم البياني
        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(data[col1], data[col2], marker='o', label='Actual Calls')
        ax.plot(future_weeks, forecast_values, marker='x', linestyle='--', label='Forecast')
        plt.xticks(rotation=45)
        ax.legend()
        st.pyplot(fig)

        # حساب الموظفين (كل موظف 2000 مكالمة في الأسبوع مثلاً)
        st.subheader("👥 Required Agents")
        agents = [int(np.ceil(v / 2000)) for v in forecast_values] # عدل رقم 2000 حسب إنتاجية الموظف عندك
        staff_df = pd.DataFrame({col1: future_weeks, 'Agents Needed': agents})
        st.table(staff_df)

    except Exception as e:
        st.error(f"Error: {e}")
