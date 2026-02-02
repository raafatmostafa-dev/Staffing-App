import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

st.set_page_config(page_title="Workforce Gap Analysis", layout="wide")

st.title("📊 Workforce Gap Analysis Calculator")
st.write("احسب الفرق بين الهيد كاونت المطلوب والحالي بناءً على الساعات")

# --- 1. إعدادات المدخلات (الـ Sidebar) ---
st.sidebar.header("⚙️ إعدادات الحساب (F3, F4, L4)")

# اختيار التواريخ لحساب NETWORKDAYS (F3, F4)
start_date = st.sidebar.date_input("Start Date (F3)", date(2024, 1, 1))
end_date = st.sidebar.date_input("End Date (F4)", date(2024, 1, 31))

# حساب أيام العمل الفعلية
start_np = np.datetime64(start_date, 'D')
end_np = np.datetime64(end_date, 'D') + np.timedelta64(1, 'D')
working_days = np.busday_count(start_np, end_np)

# نسبة الشرينكيدج (L4)
shrinkage_pct = st.sidebar.slider("Shrinkage % (L4)", 0, 100, 20) / 100

# معادلة ساعات العمل الشهرية (NETWORKDAYS * 8)
total_monthly_hours_per_agent = working_days * 8

# سعة الموظف الصافية بعد الشرينكيدج (المعادلة المطلوبة)
net_capacity_per_agent = total_monthly_hours_per_agent * (1 - shrinkage_pct)

st.sidebar.divider()
st.sidebar.write(f"📅 Working Days: **{working_days}**")
st.sidebar.write(f"⏳ Individual Net Capacity: **{round(net_capacity_per_agent, 2)}** hrs")

# --- 2. رفع الملف ---
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # قراءة الملف
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, encoding='cp1256')
        
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # تحديد الأعمدة
        col_lang = next((c for
