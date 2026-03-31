import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time
import os

# --- 1. التصميم الراقي (Elegant Design) ---
st.set_page_config(page_title="WFM Suite", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { display: none; }
    .language-card {
        background-color: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); margin-bottom: 15px;
        border-left: 6px solid #1e3a8a;
    }
    [data-testid="stMetric"] {
        background-color: #f1f5f9; padding: 15px; border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# دالة حفظ الملفات
def save_file(uploaded_file, name):
    with open(name, "wb") as f:
        f.write(uploaded_file.getbuffer())

# --- 2. الدخول والبيانات ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Access Dashboard"):
        if user == "Raafat Mostafa" and pw == "Rr#01010353831":
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

st.markdown('<h1 style="color: #1e3a8a;">Workforce Management Suite</h1>', unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity", "🎯 Requirements", "🗓️ Scheduling", "⚖️ Net Staffing"])

with tab1:
    with st.expander("⚙️ Configuration", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            d_range = st.date_input("Analysis Period", [date(2026, 4, 1), date(2026, 4, 30)])
        with c2:
            up_main = st.file_uploader("Upload Data.xlsx", type=["xlsx"])
            if up_main: save_file(up_main, "data_last.xlsx")
        with c3:
            up_intra = st.file_uploader("Upload Requirements.xlsx", type=["xlsx"])
            if up_intra: save_file(up_intra, "intra_last.xlsx")
            up_sched = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"])
            if up_sched: save_file(up_sched, "sched_last.xlsx")

    start_date, end_date = d_range[0], (d_range[1] if len(d_range) > 1 else d_range[0])
    
    if os.path.exists("data_last.xlsx"):
        df_all = pd.read_excel("data_last.xlsx")
        for _, row in df_all.iterrows():
            st.markdown(f'<div class="language-card"><h3>🚩 {row.iloc[0]}</h3></div>', unsafe_allow_html=True)
            # عرض المتركس هنا (كما في صورتك الأولى)

with tab2:
    if os.path.exists("intra_last.xlsx"):
        xls = pd.ExcelFile("intra_last.xlsx")
        langs = [s for s in xls.sheet_names if "Sheet" not in s]
        op_lang = st.selectbox("🎯 Select Language", langs)
        st.session_state['active_lang'] = op_lang
        df_intra = pd.read_excel("intra_last.xlsx", sheet_name=op_lang, header=None)
        if not df_intra.empty:
            new_cols = ["Intervals"] + [pd.to_datetime(d).strftime('%Y-%m-%d') for d in df_intra.iloc[0, 1:]]
            df_intra = df_intra.drop(0); df_intra.columns = new_cols
            df_intra.set_index("Intervals", inplace=True)
            st.session_state['df_intra_final'] = df_intra.apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
            st.dataframe(st.session_state['df_intra_final'], use_container_width=True)

with tab3:
    lang = st.session_state.get('active_lang')
    if os.path.exists("sched_last.xlsx") and lang:
        try:
            xls_s = pd.ExcelFile("sched_last.xlsx")
            sheet = next((s for s in xls_s.sheet_names if s.lower() == lang.lower()), None)
            if sheet:
                df_s = pd.read_excel("sched_last.xlsx", sheet_name=sheet)
                # مطابقة أعمدة ملفك: A=التاريخ، B=الاسم، C=البداية، D=النهاية
                df_s.columns = ['Day', 'Name', 'Start', 'End'] + list(df_s.columns[4:])
                df_s['Day'] = pd.to_datetime(df_s['Day']).dt.date
                
                intervals = pd.date_range("00:00", "23:30", freq="30min").strftime('%H:%M').tolist()
                target_dates = pd.date_range(start_date, end_date).date.tolist()
                df_cov = pd.DataFrame(0, index=intervals, columns=[d.strftime('%Y-%m-%d') for d in target_dates])

                for _, r in df_s.iterrows():
                    # معالجة ذكية للوقت (تجاهل OFF والفراغات)
                    s_raw, e_raw = str(r['Start']).upper(), str(r['End']).upper()
                    if "OFF" in s_raw or "NAN" in s_raw or s_raw == "": continue
                    
                    try:
                        s_m = pd.to_datetime(s_raw).hour * 60 + pd.to_datetime(s_raw).minute
                        e_m = pd.to_datetime(e_raw).hour * 60 + pd.to_datetime(e_raw).minute
                        d_str = r['Day'].strftime('%Y-%m-%d')
                        
                        if d_str in df_cov.columns:
                            for slot in intervals:
                                sl_m = int(slot[:2])*60 + int(slot[3:])
                                if s_m < e_m: # شيفت عادي
                                    if s_m <= sl_m < e_m: df_cov.at[slot, d_str] += 1
                                else: # شيفت ليلي
                                    if sl_m >= s_m: df_cov.at[slot, d_str] += 1
                                    elif sl_m < e_m:
                                        nxt = (r['Day'] + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                                        if nxt in df_cov.columns: df_cov.at[slot, nxt] += 1
                    except: continue
                
                st.session_state['df_cov_final'] = df_cov
                st.dataframe(df_cov.style.applymap(lambda v: 'background-color: #e3f2fd' if v > 0 else ''), use_container_width=True)
            else: st.warning("Sheet matching language not found in Schedule file.")
        except Exception as e: st.error(f"Error: {e}")

with tab4:
    if 'df_intra_final' in st.session_state and 'df_cov_final' in st.session_state:
        d_intra = st.session_state['df_intra_final']
        d_cov = st.session_state['df_cov_final'].reindex(d_intra.index).fillna(0).astype(int)
        common = [c for c in d_cov.columns if c in d_intra.columns]
        if common:
            df_gap = d_cov[common] - d_intra[common]
            def color_gap(v):
                if v < 0: return 'background-color: #fef2f2; color: #b91c1c'
                return 'background-color: #f0fdf4; color: #166534'
            st.dataframe(df_gap.style.applymap(color_gap), use_container_width=True)
