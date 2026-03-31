import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time
import os
import base64

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# دالة تحويل الصورة لخلفية
def set_bg_image(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            img_data = f.read()
        b64_encoded = base64.b64encode(img_data).decode()
        style = f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{b64_encoded}");
            background-size: cover;
            background-position: center 40%;
            background-attachment: fixed;
        }}
        </style>
        """
        st.markdown(style, unsafe_allow_html=True)

# دالة حفظ الملفات
def save_file(uploaded_file, name):
    with open(name, "wb") as f:
        f.write(uploaded_file.getbuffer())

# --- 2. نظام تسجيل الدخول ---
def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    # محاولة وضع الخلفية
    set_bg_image("background.jpg")

    st.markdown("<h2 style='color: white; text-shadow: 2px 2px 4px #000000; text-align: center;'>🔒 WFM Secure Access</h2>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("""
            <style>
            div[data-testid="stVerticalBlock"] > div:has(input) {
                background-color: rgba(255, 255, 255, 0.9);
                padding: 30px;
                border-radius: 15px;
            }
            </style>
            """, unsafe_allow_html=True)
        
        user = st.text_input("Username", key="user_input")
        pw = st.text_input("Password", type="password", key="pw_input")
        if st.button("Login", use_container_width=True):
            if user == "Raafat Mostafa" and pw == "Rr#01010353831": 
                st.session_state["authenticated"] = True
                st.rerun() 
            else:
                st.error("❌ بيانات الدخول غير صحيحة")
    return False

# --- 3. تشغيل التطبيق ---
if check_auth():
    # تنسيقات الواجهة
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { background-color: #1E1E1E !important; }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #FFFFFF !important; }
        .main-header { font-size: 1.2rem; font-weight: bold; color: #1E3A8A; border-bottom: 2px solid #EEEEEE; padding-bottom: 10px; }
        </style>
        """, unsafe_allow_html=True)

    # التبويبات
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity Dashboard", "🎯 Resource Requirements", "🗓️ Scheduling", "⚖️ Net Staffing"]) 

    with tab1:
        with st.sidebar:
            st.header("⚙️ Configuration")
            # التحقق من d_range لتجنب خطأ التواريخ
            d_range = st.date_input("Analysis Period", [date(2026, 2, 1), date(2026, 2, 28)])
            
            start_date = d_range[0]
            end_date = d_range[1] if len(d_range) > 1 else d_range[0]
            
            up_main = st.file_uploader("Upload Data.xlsx", type=["xlsx"])
            if up_main: save_file(up_main, "data_last.xlsx")
            
            up_intra = st.file_uploader("Upload Requirements.xlsx", type=["xlsx"])
            if up_intra: save_file(up_intra, "intra_last.xlsx")
            
            up_sched = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"])
            if up_sched: save_file(up_sched, "sched_last.xlsx")
            
            if st.button("Logout"):
                st.session_state["authenticated"] = False
                st.rerun()

        if os.path.exists("data_last.xlsx"):
            try:
                df_all = pd.read_excel("data_last.xlsx")
                st.markdown('<p class="main-header">🌍 Global Fleet Capacity</p>', unsafe_allow_html=True)
                st.dataframe(df_all)
            except Exception as e:
                st.error(f"Error reading Excel: {e}")
        else:
            st.info("👋 مرحباً! الرجاء رفع ملف البيانات من القائمة الجانبية.")

    # (بقية الـ Tabs بنفس المنطق مع إضافة try-except حول قراءة الملفات)
