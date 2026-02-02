import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time
import os
import base64  # مكتبة جديدة هنحتاجها لتحويل الصورة

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# دالة لتحويل الصورة المحلية لكود CSS
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(bin_file):
    bin_str = get_base64_of_bin_file(bin_file)
    page_bg_img = '''
    <style>
    .stApp {
        background-image: url("data:image/png;base64,%s");
        background-size: cover;
        background-attachment: fixed;
    }
    /* تحسين شكل التابات عشان تبان فوق الخلفية */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(255, 255, 255, 0.8);
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

# دالة حفظ الملفات لضمان ثبات البيانات
def save_file(uploaded_file, name):
    with open(name, "wb") as f:
        f.write(uploaded_file.getbuffer())

# --- 2. نظام تسجيل الدخول ---
def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    st.markdown("### 🔒 WFM Secure Access")
    col1, _ = st.columns([1, 2])
    with col1:
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if user == "Raafat Mostafa" and pw == "Rr#01010353831": 
                st.session_state["authenticated"] = True
                st.rerun() 
            else:
                st.error("❌ بيانات الدخول غير صحيحة")
    return False

# --- 3. تشغيل التطبيق بعد الدخول ---
if check_auth():
    # استدعاء صورة الخلفية (تأكد من وجود صورة باسم background.jpg في فولدر الكود)
    if os.path.exists("background.jpg"):
        set_png_as_page_bg('background.jpg')

    # CSS بتاعك الأصلي لتصغير الخط
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.85rem !important; }
        .main-header { 
            font-size: 1.2rem; 
            font-weight: bold; 
            color: #1E3A8A; 
            margin-bottom: 20px;
            background-color: rgba(255, 255, 255, 0.7);
            padding: 10px;
            border-radius: 5px;
        }
        </style>
        """, unsafe_allow_html=True)

    # --- (باقي كودك بيكمل هنا زي ما هو بالظبط بدون تغيير) ---
    def color_net_staffing(val):
        try:
            if val < 0: return 'background-color: #ffcccc; color: #900000; font-weight: bold'
            if val > 0: return 'background-color: #ccffcc; color: #006600'
        except: pass
        return ''

    def format_time_index(t):
        if isinstance(t, (time, datetime)): return t.strftime('%H:%M')
        try: return pd.to_datetime(str(t)).strftime('%H:%M')
        except: return str(t)

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity Dashboard", "⏰ Intraday", "🗓️ Scheduling", "⚖️ Net Staffing"])

    # ... (كمل باقي الأقسام tab1, tab2, tab3, tab4 زي الكود القديم بتاعك)
