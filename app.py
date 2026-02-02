import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Staffing Planner", layout="wide")

st.title("📊 Staffing & Forecasting App (Excel Version)")
st.write("ارفع ملف الإكسيل بتاعك وهحسبلك كل حاجة")

# تحديد نوع الملف إكسيل فقط
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

if uploaded_file:
    try:
        # قراءة الإكسيل
        data = pd.read_excel(uploaded_file)
        
        # تنظيف أسامي الأعمدة
        data.columns = [str(c).strip() for c in data.columns]
        
        st.subheader("📄 معاينة البيانات")
        st.dataframe(data.head())

        # بياخد أول عمود (الأسابيع) وتاني عمود (المكالمات) أياً كانت أساميهم
        col_name_1 = data.columns[0]
        col_name_2 = data.columns[1]

        # حساب التوقعات (متوسط آخر 4 أسابيع)
        avg_calls = data[col_name_2].tail(4).mean()
        
        # تجهيز الفترة القادمة (4 أسابيع مستقبلاً)
        last_val = len(data)
        future_periods = [f"Week {i}" for i in range(last_val + 1, last_val + 5)]
        forecast_values = [round(avg_calls)] * 4

        # تقسيم الشاشة
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("📈 رسم بياني للتوقعات")
            fig, ax = plt.subplots()
            ax.plot(data[col_name_1], data[col_name_2], marker='o', label='البيانات الحالية')
            ax.plot(future_periods, forecast_values, marker='x', linestyle='--', label='التوقعات المستقبيلة')
            plt.xticks(rotation=45)
            ax.legend()
            st.pyplot(fig)

        with col_right:
            st.subheader("👥 حساب عدد الموظفين")
            # تقدر تغير الرقم ده من جوه الأبلكيشن
            capacity = st.number_input("الموظف الواحد بيخلص كام مكالمة في الأسبوع؟", value=2000)
            
            needed = [int(np.ceil(v / capacity)) for v in forecast_values]
            
            res = pd.DataFrame({
                "الأسبوع القادم": future_periods,
                "المكالمات المتوقعة": forecast_values,
                "الموظفين المطلوبين": needed
            })
            st.table(res)

    except Exception as e:
        st.error(f"حصلت مشكلة وأنا بقرأ الملف: {e}")
