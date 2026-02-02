import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date

st.set_page_config(page_title="Workforce Planner Pro", layout="wide")

st.title("📊 Multi-Language Capacity Planner")
st.write("الحساب بناءً على أيام العمل الفعلية (NETWORKDAYS) لكل لغة")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # قراءة الملف
        if uploaded_file.name.endswith('.xlsx'):
            data = pd.read_excel(uploaded_file)
        else:
            data = pd.read_csv(uploaded_file, encoding='cp1256', on_bad_lines='skip')
        
        data.columns = [str(c).strip().lower() for c in data.columns]
        
        # تحديد الأعمدة
        col_lang = next((c for c in data.columns if 'lang' in c or 'لغة' in c), None)
        col_hours = next((c for c in data.columns if 'hour' in c or 'ساع' in c), None)

        if col_lang and col_hours:
            # --- قسم إعدادات التاريخ (NETWORKDAYS) ---
            st.sidebar.header("🗓️ NETWORKDAYS Settings")
            start_date = st.sidebar.date_input("Start Date (F3)", date(2024, 1, 1))
            end_date = st.sidebar.date_input("End Date (F4)", date(2024, 1, 31))
            
            # حساب أيام العمل (بايثون بياخد التاريخ النهائي حصري، فبنضيف يوم)
            # المبدأ: الإثنين-الجمعة هو الافتراضي، لو عايز السبت والأحد كأيام عمل بنغير الـ weekmask
            days = np.busday_count(str(start_date), str(pd.to_datetime(end_date) + pd.Timedelta(days=1)))
            st.sidebar.info(f"Working Days: {days}")
            
            shrinkage_pct = st.sidebar.slider("Shrinkage %", 0, 100, 20) / 100
            
            # تطبيق المعادلة: (أيام العمل * 8 ساعات) مخصوم منها الشرينكيدج
            monthly_capacity_per_agent = (days * 8) * (1 - shrinkage_pct)
            # تحويل لسعة أسبوعية للمقارنة مع داتا الأسابيع
            weekly_cap_per_agent = monthly_capacity_per_agent / 4 

            # --- الحسابات لكل لغة ---
            lang_summary = data.groupby(col_lang)[col_hours].mean().reset_index()
            lang_summary.columns = ['Language', 'Avg Weekly Target Hours']
            
            # حساب الهيد كاونت المطلوب
            lang_summary['Required HC'] = lang_summary['Avg Weekly Target Hours'].apply(
                lambda x: int(np.ceil(x / weekly_cap_per_agent)) if weekly_cap_per_agent > 0 else 0
            )

            st.subheader(f"📅 Month Analysis: {start_date} to {end_date}")
            st.table(lang_summary)

            # تفاصيل كل لغة
            st.divider()
            for index, row in lang_summary.iterrows():
                with st.expander(f"Detailed Variance: {row['Language']}"):
                    col1, col2, col3 = st.columns(3)
                    
                    actual_hc = col1.number_input(f"Actual HC ({row['Language']})", value=int(row['Required HC']), key=f"hc_{row['Language']}")
                    
                    # الساعات المتاحة من الهيد كاونت الفعلي
                    paid_hours = actual_hc * (weekly_cap_per_agent / (1 - shrinkage_pct))
                    available_hours = actual_hc * weekly_cap_per_agent
                    variance = available_hours - row['Avg Weekly Target Hours']
                    
                    col2.metric("Paid Hours (Weekly)", f"{round(paid_hours)} hr")
                    col3.metric("Variance", f"{round(variance, 1)} hr", delta=round(variance, 1))

        else:
            st.error("❌ الملف لازم يحتوي على أعمدة 'language' و 'hours'")

    except Exception as e:
        st.error(f"Error: {e}")
