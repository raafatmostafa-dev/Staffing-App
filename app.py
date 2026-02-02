import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

st.set_page_config(page_title="Custom Language Staffing", layout="wide")

st.title("📊 Language-Specific Workforce Analysis")

# --- 1. إعدادات الوقت (F3, F4) ---
st.sidebar.header("🗓️ Monthly Period (NETWORKDAYS)")
start_date = st.sidebar.date_input("Start Date (F3)", date(2024, 1, 1))
end_date = st.sidebar.date_input("End Date (F4)", date(2024, 1, 31))

# حساب أيام العمل
start_np = np.datetime64(start_date, 'D')
end_np = np.datetime64(end_date, 'D') + np.timedelta64(1, 'D')
working_days = np.busday_count(start_np, end_np)
total_hours_month = working_days * 8

st.sidebar.info(f"إجمالي ساعات العمل المتاحة (100%): {total_hours_month} ساعة")

uploaded_file = st.file_uploader("Upload Your Sheet", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # قراءة الملف
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, encoding='cp1256')
        
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # البحث عن الأعمدة
        col_lang = next((c for c in df.columns if 'lang' in c or 'لغة' in c), None)
        col_target = next((c for c in df.columns if 'target' in c or 'hour' in c or 'مطلوب' in c), None)
        col_actual_hc = next((c for c in df.columns if 'actual' in c or 'hc' in c or 'فعلي' in c), None)

        if col_lang and col_target:
            # تجميع البيانات لكل لغة
            summary = df.groupby(col_lang).agg({
                col_target: 'sum',
                col_actual_hc: 'max' if col_actual_hc else lambda x: 0
            }).reset_index()
            summary.columns = ['Language', 'Total Target Hours', 'Actual HC']

            st.subheader("📝 Calculations per Language")
            
            final_report = []
            for _, row in summary.iterrows():
                with st.expander(f"⚙️ Settings for {row['Language']}", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    # 1. إدخال الشرينكيدج لكل لغة لوحدها
                    lang_shrinkage = col1.number_input(f"Shrinkage % for {row['Language']}", value=20.0, step=1.0, key=f"shr_{row['Language']}") / 100
                    
                    # 2. الهيد كاونت (يسحب من الشيت أو تدخله لو 0)
                    actual_hc = col2.number_input(f"Actual Headcount ({row['Language']})", value=float(row['Actual HC']), key=f"hc_{row['Language']}")
                    
                    # --- تطبيق معادلاتك ---
                    # سعة الموظف بعد الشرينكيدج الخاص باللغة
                    lang_net_capacity = total_hours_month * (1 - lang_shrinkage)
                    
                    # المطلوب =
