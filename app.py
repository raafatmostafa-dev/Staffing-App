import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Staffing Planner", layout="wide")

st.title("📊 Staffing & Capacity Planner")
st.write("حساب عدد الموظفين بناءً على الساعات المطلوبة وسعة عمل الموظف")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        data = pd.read_excel(uploaded_file)
        data.columns = [str(c).strip().lower() for c in data.columns]
        
        st.subheader("📄 معاينة البيانات")
        st.dataframe(data.head())

        # البحث عن عمود الساعات (hours) وعمود الفترة (week/date)
        col_period = data.columns[0]
        col_hours = next((c for c in data.columns if 'hour' in c or 'ساع' in c), None)

        if col_hours:
            # 1. حساب متوسط الساعات المطلوبة (أسبوعياً)
            avg_required_hours = data[col_hours].tail(4).mean()
            
            # 2. إعدادات سعة الموظف (معادلتك: أيام العمل × 8 ساعات)
            st.sidebar.header("⚙️ إعدادات Capacity الموظف")
            working_days = st.sidebar.number_input("عدد أيام العمل في الشهر (Network Days)", value=22)
            daily_hours = 8
            
            # حساب سعة الموظف الشهرية والأسبوعية
            monthly_capacity = working_days * daily_hours
            weekly_capacity = monthly_capacity / 4  # عشان نقارن أسبوع بأسبوع

            # 3. النتائج
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("متوسط الساعات المطلوبة (أسبوعياً)", f"{round(avg_required_hours, 1)} hr")
            c2.metric("سعة الموظف الأسبوعية", f"{weekly_capacity} hr")
            
            # حساب الموظفين: الساعات المطلوبة ÷ سعة الموظف الواحدة
            needed_agents = int(np.ceil(avg_required_hours / weekly_capacity))
            c3.metric("عدد الموظفين المطلوبين", f"{needed_agents} Agents")

            # الرسم البياني للمقارنة
            st.subheader("📊 Comparison: Load vs Capacity")
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.barh(["Workload (Hours)", "Agent Capacity"], [avg_required_hours, weekly_capacity], color=['#FF4B4B', '#00CC96'])
            st.pyplot(fig)
            
            if avg_required_hours > weekly_capacity * needed_agents:
                st.warning("⚠️ تنبيه: عدد الموظفين قد لا يكفي لتغطية الساعات المطلوبة بدقة.")
            else:
                st.success(f"✅ تم الحساب: لتغطية {round(avg_required_hours)} ساعة أسبوعياً، تحتاج إلى {needed_agents} موظفين.")
        else:
            st.error("❌ لم يتم العثور على عمود باسم 'hours' في الملف.")

    except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة: {e}")
