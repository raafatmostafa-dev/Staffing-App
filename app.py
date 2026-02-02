import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

# إعدادات الصفحة
st.set_page_config(page_title="WFM Ultimate Dashboard", layout="wide")

# --- تحسين الواجهة CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    .report-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #1E3A8A;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .metric-label { color: #64748B; font-size: 14px; font-weight: bold; }
    .metric-value { color: #1E3A8A; font-size: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Workforce Comprehensive Analysis")
st.markdown("---")

# --- Sidebar ---
with st.sidebar:
    st.header("📅 Period Settings")
    start_date = st.date_input("Start Date (F3)", date(2026, 2, 1))
    end_date = st.date_input("End Date (F4)", date(2026, 2, 28))
    
    # حساب NETWORKDAYS
    start_np = np.datetime64(start_date, 'D')
    end_np = np.datetime64(end_date, 'D') + np.timedelta64(1, 'D')
    working_days = np.busday_count(start_np, end_np)
    base_hours = working_days * 8
    
    st.metric("Working Days", working_days)
    st.metric("Total Base Hours", base_hours)
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload Data.xlsx", type=["xlsx"])

# --- العرض الرئيسي ---
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # تعيين أسماء الأعمدة من ملفك
        col_lang = "languages"
        col_target_hrs = "monthly target hours hours"
        col_actual_hc = "actual hc"
        col_shr = "shrinkage"

        st.subheader("📋 Language Performance Metrics")

        for _, row in df.iterrows():
            lang = row[col_lang]
            target_hrs = row[col_target_hrs]
            
            # القيم الافتراضية من الملف
            init_hc = float(row[col_actual_hc])
            init_shr = float(row[row[col_shr]]) * 100 if float(row[col_shr]) < 1 else float(row[col_shr])

            # حسابات المعادلات
            with st.container():
                st.markdown(f"#### 🌐 {lang}")
                
                # منطقة المدخلات (بسيطة في سطر واحد)
                input_col1, input_col2 = st.columns([1, 1])
                user_hc = input_col1.number_input(f"Edit Actual HC ({lang})", value=init_hc, key=f"hc_{lang}")
                user_shr = input_col2.number_input(f"Edit Shrinkage % ({lang})", value=init_shr, key=f"sh_{lang}") / 100
                
                # الحسابات الأساسية
                net_cap = base_hours * (1 - user_shr)
                req_hc = np.ceil(target_hrs / net_cap) if net_cap > 0 else 0
                avail_hrs = user
