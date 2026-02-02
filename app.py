import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date

st.set_page_config(page_title="Workforce Planner Pro", layout="wide")

st.title("📊 Multi-Language Capacity Planner")
st.write("الحساب بناءً على أيام العمل الفعلية (NETWORKDAYS)")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # قراءة الملف
        if uploaded_file.name.endswith('.xlsx'):
            data = pd.read_excel(uploaded_file)
        else:
            data = pd.read_csv(uploaded_file, encoding='cp1256', on_bad_lines='skip')
        
        data.columns = [str(c).strip().lower() for c in data.columns]
        
        col_lang = next((c for c in data.columns if 'lang' in c or 'لغة' in c), None)
        col_hours = next((c for c in data.columns if 'hour' in c or 'ساع' in c), None)

        if col_lang and col_hours:
            # --- قسم إعدادات التاريخ ---
            st.sidebar.header("🗓️ NETWORKDAYS Settings")
            start_date = st.sidebar.date_input("Start Date (F3)", date(2024, 1, 1))
            end_date = st.sidebar.date_input("End Date (F4)", date(2024, 1, 31))
            
            # الحل هنا: بنحول التواريخ لـ string وبعدين لـ datetime64[D] عشان الأيرور يختفي
            start_np = np.datetime64(start_date, 'D')
            end_np = np.datetime64(end_date, 'D') + np.timedelta64(1, 'D')
            
            # حساب أيام العمل (بديل NETWORKDAYS)
            working_days = np.busday_count(start_np, end_np)
            st.sidebar.info(f"Working Days: {working_days} days")
            
            shrinkage_pct = st.sidebar.slider("Shrinkage %", 0, 100, 20) / 100
            
            # تطبيق المعادلة: (أيام العمل * 8 ساعات) مخصوم منها الشرينكيدج
            monthly_capacity_per_agent = (working_days * 8) * (1 - shrinkage_pct)
            weekly_cap_per_agent = monthly_capacity_per_agent / 4 

            # --- الحسابات لكل لغة ---
            lang_summary = data.groupby(col_lang)[col_hours].mean().reset_index()
            lang_summary.columns = ['Language', 'Avg Weekly Target Hours']
            
            lang_summary['Required HC'] = lang_summary['Avg Weekly Target Hours'].apply(
                lambda x: int(np.ceil(x / weekly_cap_per_agent)) if weekly_cap_per_agent > 0 else 0
            )

            st.subheader(f"📅 Analysis for {working_days} Working Days")
            st.table(lang_summary)

            # تفاصيل كل لغة والـ Variance
            st.divider()
            for index, row in lang_summary.iterrows():
                with st.expander(f"Detailed Variance: {row['Language']}"):
                    col1, col2, col3 = st.columns(3)
                    actual_hc = col1.number_input(f"Actual HC ({row['Language']})", value=int(row['Required HC']), key=f"hc_{row['Language']}")
                    
                    available_hours = actual_hc * weekly_cap_per_agent
                    variance = available_hours - row['Avg Weekly Target Hours']
                    
                    col2.metric("Available Hours (Weekly)", f"{round(available_hours, 1)} hr")
                    col3.metric("Variance", f"{round(variance, 1)} hr", delta=round(variance, 1))

        else:
            st.error("❌ تأكد من وجود أعمدة 'language' و 'hours' في الملف.")

    except Exception as e:
        st.error(f"Error: {e}")
