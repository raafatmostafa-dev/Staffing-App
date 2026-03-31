import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time
import os
import base64

# --- 1. إعدادات الصفحة والتصميم الفاخر ---
st.set_page_config(page_title="WFM Professional Suite", layout="wide", initial_sidebar_state="collapsed")

# تصميم CSS مخصص "Elegant & Chic View"
st.markdown("""
    <style>
    /* تحسين الخلفية العامة */
    .stApp { background-color: #f8f9fa; }
    
    /* إخفاء الشريط الجانبي تماماً */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="stSidebarNav"] { display: none; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* تصميم التبويبات (Tabs) */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: white; border-radius: 12px 12px 0px 0px;
        padding: 10px 25px; font-weight: 600; color: #4b5563; border: none;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important; color: #1e3a8a !important;
        border-bottom: 3px solid #1e3a8a !important;
    }

    /* كروت اللغات */
    .language-card {
        background-color: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); margin-bottom: 15px;
        border-left: 6px solid #1e3a8a;
    }

    /* تحسين المقاييس (Metrics) */
    [data-testid="stMetric"] {
        background-color: #f1f5f9; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0;
    }
    [data-testid="stMetricLabel"] { font-weight: 700 !important; color: #64748b !important; font-size: 0.8rem !important; }
    [data-testid="stMetricValue"] { color: #1e3a8a !important; font-size: 1.3rem !important; }

    /* العناوين والأزرار */
    .main-title { color: #1e3a8a; font-weight: 800; font-size: 2.2rem; margin-bottom: 20px; letter-spacing: -1px; }
    .stButton>button {
        border-radius: 10px; background-color: #1e3a8a; color: white;
        border: none; transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #2563eb; transform: translateY(-2px); }
    </style>
    """, unsafe_allow_html=True)

# دالات مساعدة
def save_file(uploaded_file, name):
    with open(name, "wb") as f:
        f.write(uploaded_file.getbuffer())

def color_net_staffing(val):
    try:
        if val < 0: return 'background-color: #ffebee; color: #b71c1c; font-weight: bold'
        if val > 0: return 'background-color: #e8f5e9; color: #1b5e20'
    except: pass
    return ''

# --- 2. نظام تسجيل الدخول ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<div style='text-align: center; margin-top: 100px;'><h1 style='color:#1e3a8a;'>🔒 WFM Secure Login</h1></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Access Dashboard", use_container_width=True):
            if user == "Raafat Mostafa" and pw == "Rr#01010353831":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Invalid Credentials")
    st.stop()

# --- 3. محتوى البرنامج الرئيسي ---
st.markdown('<h1 class="main-title">Workforce Management Suite</h1>', unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity Dashboard", "🎯 Resource Req", "🗓️ Scheduling", "⚖️ Net Staffing"])

with tab1:
    with st.expander("⚙️ Configuration & Data Source", expanded=False):
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
            if st.button("Sign Out"):
                st.session_state["authenticated"] = False
                st.rerun()

    start_date = d_range[0]
    end_date = d_range[1] if len(d_range) > 1 else d_range[0]

    if os.path.exists("data_last.xlsx"):
        df_all = pd.read_excel("data_last.xlsx", sheet_name=0)
        working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
        base_hrs_per_person = working_days * 8

        for _, row in df_all.iterrows():
            lang = str(row.iloc[0]); target_hrs = float(row.iloc[1])
            act_hc = float(row.iloc[2]); shrink = float(row.iloc[3])
            shrink_p = shrink / 100 if shrink > 1 else shrink
            
            act_hrs = (act_hc * base_hrs_per_person) * (1 - shrink_p)
            req_hc = np.ceil(target_hrs / (base_hrs_per_person * (1 - shrink_p))) if base_hrs_per_person > 0 else 0
            
            st.markdown(f'<div class="language-card"><h3>🚩 {lang.upper()}</h3></div>', unsafe_allow_html=True)
            m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
            m1.metric("Tgt Hrs", f"{int(target_hrs):,}h")
            m2.metric("Act Hrs", f"{int(act_hrs):,}h")
            m3.metric("Hrs Var", f"{int(act_hrs - target_hrs):,}h", delta=int(act_hrs - target_hrs))
            m4.metric("Shrink", f"{shrink_p*100:.1f}%")
            m5.metric("Req HC", f"{int(req_hc)}")
            m6.metric("Act HC", f"{int(act_hc)}")
            m7.metric("HC Gap", f"{int(act_hc - req_hc)}", delta=int(act_hc - req_hc))

with tab2:
    if os.path.exists("intra_last.xlsx"):
        xls = pd.ExcelFile("intra_last.xlsx")
        avail_langs = [s for s in xls.sheet_names if "Sheet" not in s]
        op_lang = st.selectbox("🎯 Active Language Scope", avail_langs)
        st.session_state['active_lang'] = op_lang
        
        df_raw = pd.read_excel("intra_last.xlsx", sheet_name=op_lang, header=None)
        if not df_raw.empty:
            new_cols = ["Intervals"] + [pd.to_datetime(d).strftime('%Y-%m-%d') for d in df_raw.iloc[0, 1:]]
            df_intra = df_raw.drop(0).copy()
            df_intra.columns = new_cols
            df_intra.set_index("Intervals", inplace=True)
            final_df = df_intra.apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
            st.session_state['df_intra'] = final_df
            st.dataframe(final_df, use_container_width=True)

with tab3:
    lang = st.session_state.get('active_lang')
    if os.path.exists("sched_last.xlsx") and lang:
        st.subheader(f"🗓️ Workforce Coverage: {lang}")
        try:
            df_s = pd.read_excel("sched_last.xlsx", sheet_name=lang)
            df_s.columns = ['Day', 'Name', 'Start Time', 'End Time'] + list(df_s.columns[4:])
            df_s['Day'] = pd.to_datetime(df_s['Day']).dt.date
            
            intervals = pd.date_range("00:00", "23:30", freq="30min").strftime('%H:%M').tolist()
            target_dates = pd.date_range(start_date, end_date).date.tolist()
            df_cov = pd.DataFrame(0, index=intervals, columns=[d.strftime('%Y-%m-%d') for d in target_dates])

            def to_min(t_input):
                if isinstance(t_input, (datetime, time)): return t_input.hour * 60 + t_input.minute
                ts = pd.to_datetime(str(t_input))
                return ts.hour * 60 + ts.minute

            for _, r in df_s.iterrows():
                if pd.isna(r['Day']): continue
                st_str, en_str = str(r['Start Time']).upper(), str(r['End Time']).upper()
                if "OFF" in st_str or "NAN" in st_str: continue

                try:
                    s_m = to_min(r['Start Time']); e_m = to_min(r['End Time'])
                    for slot in intervals:
                        sl_m = datetime.strptime(slot, '%H:%M').hour * 60 + datetime.strptime(slot, '%H:%M').minute
                        d_str = r['Day'].strftime('%Y-%m-%d')
                        if d_str not in df_cov.columns: continue

                        if s_m < e_m:
                            if s_m <= sl_m < e_m: df_cov.at[slot, d_str] += 1
                        else: # Night Shift
                            if sl_m >= s_m: df_cov.at[slot, d_str] += 1
                            elif sl_m < e_m:
                                nxt = (r['Day'] + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                                if nxt in df_cov.columns: df_cov.at[slot, nxt] += 1
                except: continue

            st.session_state['df_cov'] = df_cov
            st.dataframe(df_cov.style.background_gradient(cmap="Blues"), use_container_width=True)
        except Exception as e: st.error(f"Error: {e}")

with tab4:
    lang = st.session_state.get('active_lang')
    if 'df_intra' in st.session_state and 'df_cov' in st.session_state:
        st.subheader(f"⚖️ Efficiency Gap: {lang}")
        d_intra = st.session_state['df_intra']
        d_cov = st.session_state['df_cov'].reindex(d_intra.index).fillna(0).astype(int)
        common = [c for c in d_cov.columns if c in d_intra.columns]
        if common:
            df_net = d_cov[common] - d_intra[common]
            st.dataframe(df_net.style.map(color_net_staffing), use_container_width=True)
    else: st.info("Please upload data and select a language first.")
