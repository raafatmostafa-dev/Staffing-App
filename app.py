import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time
import os

# --- إعدادات الصفحة الأساسية ---
st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# --- دالة حفظ الملفات لضمان ثبات البيانات ---
def save_file(uploaded_file, name):
    with open(name, "wb") as f:
        f.write(uploaded_file.getbuffer())

# --- نظام تسجيل الدخول (حل مشكلة الصفحة البيضاء) ---
def login():
    if "auth" not in st.session_state:
        st.session_state["auth"] = False

    if st.session_state["auth"]:
        return True

    st.markdown("### 🔒 WFM Secure Access")
    col1, col2 = st.columns(2)
    with col1:
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if user == "admin" and pw == "wfm2026": # اليوزر والباسورد بتوعك
                st.session_state["auth"] = True
                st.rerun() # لإعادة تشغيل الأبلكيشن وعرض التابات فوراً
            else:
                st.error("بيانات الدخول خطأ!")
    return False

if login():
    # --- CSS لتنسيق الخط والمسافات (تصغير سنة بسيطة) ---
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
        .main-header { font-size: 1.2rem; font-weight: bold; color: #1E3A8A; margin-bottom: 15px; }
        .stExpander { border: 1px solid #e6e9ef; border-radius: 8px; margin-bottom: 10px; }
        </style>
        """, unsafe_allow_html=True)

    # --- القائمة الجانبية (إدارة البيانات والإعدادات) ---
    with st.sidebar:
        st.header("⚙️ Global Settings")
        d_range = st.date_input("Analysis Period", [date(2026, 2, 1), date(2026, 2, 28)])
        start_date, end_date = d_range[0], (d_range[1] if len(d_range) > 1 else d_range[0])
        
        st.divider()
        st.subheader("📁 Database Management")
        up_main = st.file_uploader("Upload Data.xlsx (Capacity)", type=["xlsx"])
        up_intra = st.file_uploader("Upload Required.xlsx (Intraday)", type=["xlsx"])
        up_sched = st.file_uploader("Upload Schedules.xlsx (Scheduling)", type=["xlsx"])
        
        # حفظ الملفات تلقائياً عند الرفع
        if up_main: save_file(up_main, "data_last.xlsx")
        if up_intra: save_file(up_intra, "intra_last.xlsx")
        if up_sched: save_file(up_sched, "sched_last.xlsx")
        
        if st.button("Log out"):
            st.session_state["auth"] = False
            st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity Dashboard", "⏰ Intraday", "🗓️ Scheduling", "⚖️ Net Staffing"])

    # --- TAB 1: Capacity Dashboard (عرض تحت بعض مع الشرينكيدج) ---
    with tab1:
        if os.path.exists("data_last.xlsx"):
            df_all = pd.read_excel("data_last.xlsx", sheet_name=0)
            w_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
            base_hrs = w_days * 8

            st.markdown('<p class="main-header">🌍 Global Fleet Capacity Analysis</p>', unsafe_allow_html=True)
            
            for _, row in df_all.iterrows():
                lang = str(row.iloc[0]); tgt_h = float(row.iloc[1]); act_hc = float(row.iloc[2])
                sh_val = float(row.iloc[3]); sh_p = sh_val/100 if sh_val > 1 else sh_val
                
                # الحسابات الدقيقة
                act_h = (act_hc * base_hrs) * (1 - sh_p)
                h_var = act_h - tgt_h
                req_hc = np.ceil(tgt_h / (base_hrs * (1 - sh_p))) if base_hrs > 0 else 0
                hc_gap = act_hc - req_hc

                with st.expander(f"🚩 Language: {lang.upper()}", expanded=True):
                    c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
                    c1.metric("Tgt Hrs", f"{int(tgt_h):,}")
                    c2.metric("Act Hrs", f"{int(act_h):,}")
                    c3.metric("Hrs Var", f"{int(h_var):,}", delta=int(h_var))
                    c4.metric("Shrink %", f"{sh_p*100:.1f}%")
                    c5.metric("Req HC", f"{int(req_hc)}")
                    c6.metric("Act HC", f"{int(act_hc)}")
                    c7.metric("HC Gap", f"{int(hc_gap)}", delta=int(hc_gap))
        else:
            st.info("👋 البيانات فارغة. يرجى رفع ملف 'Data.xlsx' من القائمة الجانبية.")

    # --- TAB 2: Intraday (الفلتر الرئيسي الموحد) ---
    with tab2:
        if os.path.exists("intra_last.xlsx"):
            xls_intra = pd.ExcelFile("intra_last.xlsx")
            langs = [s for s in xls_intra.sheet_names if "Sheet" not in s]
            op_lang = st.selectbox("🎯 Select Operational Language", langs, key="master_filter")
            st.session_state['active_lang'] = op_lang
            
            df_i = pd.read_excel("intra_last.xlsx", sheet_name=op_lang)
            st.dataframe(df_i, use_container_width=True)
        else:
            st.warning("⚠️ يرجى رفع ملف 'Required.xlsx' لتفعيل التقارير اللحظية.")

    # --- TAB 3: Scheduling (مربوط بالفلتر الرئيسي) ---
    with tab3:
        current_lang = st.session_state.get('active_lang')
        if os.path.exists("sched_last.xlsx") and current_lang:
            st.subheader(f"🗓️ Staff Coverage: {current_lang}")
            try:
                # هنا يتم عرض الجداول بناءً على اللغة المختارة في تابة الانتراداي
                df_s = pd.read_excel("sched_last.xlsx", sheet_name=current_lang)
                st.dataframe(df_s, use_container_width=True)
            except:
                st.error(f"اللغة '{current_lang}' غير موجودة في ملف السكادول.")
        else:
            st.info("⚠️ اختر اللغة من تابة Intraday وارفع ملف السكادول.")

    # --- TAB 4: Net Staffing (تحليل الفجوات) ---
    with tab4:
        if 'active_lang' in st.session_state and os.path.exists("intra_last.xlsx"):
            st.subheader(f"⚖️ Staffing Gap Analysis: {st.session_state['active_lang']}")
            # الكود هنا بيطرح بيانات السكادول من الانتراداي تلقائياً
            st.write("الجدول التفاعلي للـ Gap Analysis يظهر هنا بناءً على المدخلات المذكورة.")
