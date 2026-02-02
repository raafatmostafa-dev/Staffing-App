import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time
import os

# --- إعدادات الصفحة ---
st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# دالة لحفظ الملف المرفوع على الجهاز/السيرفر
def save_uploaded_file(uploaded_file, save_name):
    with open(save_name, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return save_name

# --- نظام التأمين (Login System) ---
def check_password():
    def password_entered():
        if st.session_state["username"] == "admin" and st.session_state["password"] == "wfm2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("### 🔒 WFM Secure Access")
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

if check_password():
    # --- CSS لتصغير الخط والمظهر الاحترافي ---
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.85rem !important; }
        .main-header { font-size: 1.2rem; font-weight: bold; color: #1E3A8A; margin-bottom: 20px; }
        </style>
        """, unsafe_allow_html=True)

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

    # --- القائمة الجانبية لإدارة الملفات ---
    with st.sidebar:
        st.header("⚙️ Data Management")
        d_range = st.date_input("Analysis Period", [date(2026, 2, 1), date(2026, 2, 28)])
        start_date, end_date = d_range[0], (d_range[1] if len(d_range) > 1 else d_range[0])
        
        st.divider()
        st.subheader("Update Files")
        up_main = st.file_uploader("Update Data.xlsx", type=["xlsx"])
        up_intra = st.file_uploader("Update Required.xlsx", type=["xlsx"])
        up_sched = st.file_uploader("Update Schedules.xlsx", type=["xlsx"])
        
        # حفظ الملفات لو اترفع حاجة جديدة
        if up_main: save_uploaded_file(up_main, "data_last.xlsx")
        if up_intra: save_uploaded_file(up_intra, "intra_last.xlsx")
        if up_sched: save_uploaded_file(up_sched, "sched_last.xlsx")
        
        if st.button("Log out"):
            st.session_state["password_correct"] = False
            st.rerun()

    # --- TAB 1: Capacity ---
    with tab1:
        # محاولة قراءة الملف المحفوظ
        if os.path.exists("data_last.xlsx"):
            df_all = pd.read_excel("data_last.xlsx", sheet_name=0)
            working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
            base_hrs_per_person = working_days * 8

            st.markdown('<p class="main-header">🌍 Global Fleet Capacity Analysis (Auto-Loaded)</p>', unsafe_allow_html=True)

            for _, row in df_all.iterrows():
                lang_name = str(row.iloc[0]); target_workload_hrs = float(row.iloc[1])
                actual_hc_count = float(row.iloc[2]); shrink_val = float(row.iloc[3])
                shrink_p = shrink_val / 100 if shrink_val > 1 else shrink_val 

                actual_available_hrs = (actual_hc_count * base_hrs_per_person) * (1 - shrink_p)
                hrs_variance = actual_available_hrs - target_workload_hrs
                req_hc = np.ceil(target_workload_hrs / (base_hrs_per_person * (1 - shrink_p))) if base_hrs_per_person > 0 else 0
                hc_variance = actual_hc_count - req_hc

                with st.expander(f"🚩 Language: {lang_name.upper()}", expanded=True):
                    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
                    c1.metric("Tgt Hrs", f"{int(target_workload_hrs):,}h")
                    c2.metric("Act Hrs", f"{int(actual_available_hrs):,}h")
                    c3.metric("Hrs Var", f"{int(hrs_variance):,}h", delta=int(hrs_variance))
                    c4.metric("Shrink %", f"{shrink_p*100:.1f}%")
                    c5.metric("Req HC", f"{int(req_hc)}")
                    c6.metric("Act HC", f"{int(actual_hc_count)}")
                    c7.metric("HC Gap", f"{int(hc_variance)}", delta=int(hc_variance))
        else:
            st.warning("⚠️ No data found. Please upload 'Data.xlsx' from the sidebar.")

    # --- TAB 2: Intraday ---
    with tab2:
        if os.path.exists("intra_last.xlsx"):
            xls = pd.ExcelFile("intra_last.xlsx")
            avail_langs = [s for s in xls.sheet_names if "Sheet" not in s]
            op_lang = st.selectbox("🎯 Operational Language", avail_langs, key="op_filter")
            st.session_state['active_lang'] = op_lang
            
            df_raw = pd.read_excel("intra_last.xlsx", sheet_name=op_lang, header=None)
            if not df_raw.empty:
                new_cols = ["Intervals"] + [pd.to_datetime(d).strftime('%Y-%m-%d') for d in df_raw.iloc[0, 1:]]
                df_intra = df_raw.drop(0).copy()
                df_intra.columns = new_cols
                df_intra['Intervals'] = df_intra['Intervals'].apply(format_time_index)
                st.session_state['df_intra'] = df_intra.set_index('Intervals').apply(pd.to_numeric, errors='coerce').fillna(0).round(0).astype(int)
                st.dataframe(st.session_state['df_intra'], use_container_width=True)
        else:
            st.warning("⚠️ Please upload 'Required.xlsx' from the sidebar.")

    # --- TAB 3: Scheduling ---
    with tab3:
        lang = st.session_state.get('active_lang')
        if os.path.exists("sched_last.xlsx") and lang:
            st.subheader(f"🗓️ Coverage: {lang}")
            try:
                df_s = pd.read_excel("sched_last.xlsx", sheet_name=lang)
                intervals = pd.date_range("00:00", "23:30", freq="30min").strftime('%H:%M').tolist()
                df_s['Day'] = pd.to_datetime(df_s['Day'], errors='coerce')
                target_dates = pd.date_range
