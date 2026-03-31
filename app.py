import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time
import os

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="WFM Professional Suite", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { display: none; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: white; border-radius: 12px 12px 0px 0px;
        padding: 10px 25px; font-weight: 600; color: #4b5563; box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    .stTabs [aria-selected="true"] {
        color: #1e3a8a !important; border-bottom: 3px solid #1e3a8a !important;
    }

    .language-card {
        background-color: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); margin-bottom: 15px;
        border-left: 6px solid #1e3a8a;
    }

    [data-testid="stMetric"] { background-color: #f1f5f9; padding: 15px; border-radius: 12px; }
    .main-title { color: #1e3a8a; font-weight: 800; font-size: 2.2rem; margin-bottom: 20px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

def save_file(uploaded_file, name):
    with open(name, "wb") as f:
        f.write(uploaded_file.getbuffer())

def color_net_staffing(val):
    if val < 0: return 'background-color: #ffebee; color: #b71c1c; font-weight: bold'
    if val > 0: return 'background-color: #e8f5e9; color: #1b5e20'
    return ''

# --- 2. نظام تسجيل الدخول ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h2 style='text-align:center;'>🔒 Login</h2>", unsafe_allow_html=True)
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if user == "Raafat Mostafa" and pw == "Rr#01010353831":
                st.session_state["authenticated"] = True
                st.rerun()
            else: st.error("❌ بيانات خاطئة")
    st.stop()

# --- 3. محتوى البرنامج الرئيسي ---
st.markdown('<h1 class="main-title">Workforce Management Suite</h1>', unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity", "🎯 Resource Req", "🗓️ Scheduling", "⚖️ Net Staffing"])

with tab1:
    with st.expander("⚙️ Configuration & Uploads", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            d_range = st.date_input("Period", [date(2026, 4, 1), date(2026, 4, 30)])
        with c2:
            up_main = st.file_uploader("Data.xlsx", type=["xlsx"])
            if up_main: save_file(up_main, "data_last.xlsx")
        with c3:
            up_intra = st.file_uploader("Required.xlsx", type=["xlsx"])
            if up_intra: save_file(up_intra, "intra_last.xlsx")
            up_sched = st.file_uploader("Schedules.xlsx", type=["xlsx"])
            if up_sched: save_file(up_sched, "sched_last.xlsx")

    start_date, end_date = d_range[0], (d_range[1] if len(d_range) > 1 else d_range[0])

with tab2:
    if os.path.exists("intra_last.xlsx"):
        xls = pd.ExcelFile("intra_last.xlsx")
        langs = [s for s in xls.sheet_names if "Sheet" not in s]
        op_lang = st.selectbox("Select Language", langs)
        st.session_state['active_lang'] = op_lang
        df_raw = pd.read_excel("intra_last.xlsx", sheet_name=op_lang, header=None)
        if not df_raw.empty:
            new_cols = ["Intervals"] + [pd.to_datetime(d).strftime('%Y-%m-%d') for d in df_raw.iloc[0, 1:]]
            df_intra = df_raw.drop(0).copy()
            df_intra.columns = new_cols
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
                df_s.columns = ['Day', 'Name', 'Start', 'End'] + list(df_s.columns[4:])
                df_s['Day'] = pd.to_datetime(df_s['Day']).dt.date
                
                intervals = pd.date_range("00:00", "23:30", freq="30min").strftime('%H:%M').tolist()
                target_dates = pd.date_range(start_date, end_date).date.tolist()
                df_cov = pd.DataFrame(0, index=intervals, columns=[d.strftime('%Y-%m-%d') for d in target_dates])

                def to_min(v):
                    v_str = str(v).strip().upper()
                    if v_str in ["OFF", "NAN", ""] or "OFF" in v_str: return None
                    try:
                        t = pd.to_datetime(v_str).time()
                        return t.hour * 60 + t.minute
                    except: return None

                for _, r in df_s.iterrows():
                    s_m, e_m = to_min(r['Start']), to_min(r['End'])
                    if s_m is None or pd.isna(r['Day']): continue
                    
                    d_str = r['Day'].strftime('%Y-%m-%d')
                    if d_str in df_cov.columns:
                        for slot in intervals:
                            sl_m = int(slot[:2])*60 + int(slot[3:])
                            if s_m < e_m: # شيفت نهاري
                                if s_m <= sl_m < e_m: df_cov.at[slot, d_str] += 1
                            else: # شيفت ليلي
                                if sl_m >= s_m or sl_m < e_m:
                                    target_day = d_str if sl_m >= s_m else (r['Day'] + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                                    if target_day in df_cov.columns: df_cov.at[slot, target_day] += 1
                
                st.session_state['df_cov_final'] = df_cov
                st.dataframe(df_cov, use_container_width=True)
        except Exception as e: st.error(f"Error: {e}")

with tab4:
    # المعادلة: Tab 3 (Scheduling) - Tab 2 (Resource Req)
    if 'df_intra_final' in st.session_state and 'df_cov_final' in st.session_state:
        d_req = st.session_state['df_intra_final']
        d_sch = st.session_state['df_cov_final']
        
        # محاذاة البيانات لضمان الطرح الصحيح لكل يوم وساعة
        d_sch_aligned = d_sch.reindex(index=d_req.index, columns=d_req.columns).fillna(0).astype(int)
        
        st.subheader(f"⚖️ Net Staffing (Schedules - Required): {st.session_state.get('active_lang')}")
        
        # العملية الحسابية المطلوبة: 3 - 2
        df_net = d_sch_aligned - d_req 
        
        st.dataframe(df_net.style.applymap(color_net_staffing), use_container_width=True)
    else:
        st.info("الرجاء رفع الملفات واختيار اللغة أولاً.")
