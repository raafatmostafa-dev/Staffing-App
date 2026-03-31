import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time
import os

# --- 1. إعدادات الصفحة والتصميم (Elegant Design) ---
st.set_page_config(page_title="WFM Professional Suite", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { display: none; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* تصميم التبويبات */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: white; border-radius: 12px 12px 0px 0px;
        padding: 10px 25px; font-weight: 600; color: #4b5563;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    .stTabs [aria-selected="true"] {
        color: #1e3a8a !important; border-bottom: 3px solid #1e3a8a !important;
    }

    /* كروت البيانات */
    .language-card {
        background-color: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); margin-bottom: 15px;
        border-left: 6px solid #1e3a8a;
    }

    .main-title { color: #1e3a8a; font-weight: 800; font-size: 2.2rem; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# دالات مساعدة
def save_file(uploaded_file, name):
    with open(name, "wb") as f:
        f.write(uploaded_file.getbuffer())

def color_net_staffing(val):
    if val < 0: return 'background-color: #ffebee; color: #b71c1c; font-weight: bold' # عجز
    if val > 0: return 'background-color: #e8f5e9; color: #1b5e20' # زيادة
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
            else: st.error("❌ بيانات الدخول غير صحيحة")
    st.stop()

# --- 3. التطبيق الرئيسي ---
st.markdown('<h1 class="main-title">Workforce Management Suite</h1>', unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity", "🎯 Resource Req", "🗓️ Scheduling", "⚖️ Net Staffing"])

with tab1:
    with st.expander("⚙️ Configuration & Uploads", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            d_range = st.date_input("Analysis Period", [date(2026, 4, 1), date(2026, 4, 30)]) #
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
        working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
        base_hrs = working_days * 8
        for _, row in df_all.iterrows():
            lang, tgt, act_hc, shr = str(row.iloc[0]), float(row.iloc[1]), float(row.iloc[2]), float(row.iloc[3])
            shr_p = shr/100 if shr > 1 else shr
            avail_hrs = (act_hc * base_hrs) * (1 - shr_p)
            req_hc = np.ceil(tgt / (base_hrs * (1 - shr_p))) if base_hrs > 0 else 0
            
            st.markdown(f'<div class="language-card"><h3>🚩 {lang.upper()}</h3></div>', unsafe_allow_html=True)
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Tgt Hrs", f"{int(tgt):,}h")
            m2.metric("Act Hrs", f"{int(avail_hrs):,}h")
            m3.metric("Hrs Var", f"{int(avail_hrs-tgt):,}", delta=int(avail_hrs-tgt))
            m4.metric("Req HC", int(req_hc))
            m5.metric("Act HC", int(act_hc))
            m6.metric("HC Gap", int(act_hc-req_hc), delta=int(act_hc-req_hc)) #

with tab2:
    if os.path.exists("intra_last.xlsx"):
        xls = pd.ExcelFile("intra_last.xlsx")
        avail_langs = [s for s in xls.sheet_names if "Sheet" not in s]
        op_lang = st.selectbox("🎯 Select Language", avail_langs) #
        st.session_state['active_lang'] = op_lang
        df_raw = pd.read_excel("intra_last.xlsx", sheet_name=op_lang, header=None)
        if not df_raw.empty:
            cols = ["Intervals"] + [pd.to_datetime(d).strftime('%Y-%m-%d') for d in df_raw.iloc[0, 1:]]
            df_intra = df_raw.drop(0); df_intra.columns = cols
            df_intra.set_index("Intervals", inplace=True)
            st.session_state['df_intra_final'] = df_intra.apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
            st.dataframe(st.session_state['df_intra_final'], use_container_width=True) #

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

                def to_min(v):
                    if pd.isna(v) or str(v).strip().upper() in ["OFF", "NAN", ""]: return None #
                    return pd.to_datetime(str(v)).hour * 60 + pd.to_datetime(str(v)).minute

                for _, r in df_s.iterrows():
                    s_m, e_m = to_min(r['Start']), to_min(r['End'])
                    if s_m is None or pd.isna(r['Day']): continue
                    d_str = r['Day'].strftime('%Y-%m-%d')
                    if d_str in df_cov.columns:
                        for slot in intervals:
                            sl_m = int(slot[:2])*60 + int(slot[3:])
                            if s_m < e_m: # شيفت نهاري
                                if s_m <= sl_m < e_m: df_cov.at[slot, d_str] += 1
                            else: # شيفت ليلي (منتصف الليل)
                                if sl_m >= s_m or sl_m < e_m: df_cov.at[slot, d_str] += 1
                
                st.session_state['df_cov_final'] = df_cov
                st.dataframe(df_cov.style.applymap(lambda v: 'background-color: #e3f2fd' if v > 0 else ''), use_container_width=True) #
        except Exception as e: st.error(f"Error: {e}")

with tab4:
    # الحساب النهائي: السكادول ناقص الريكوايرد
    if 'df_intra_final' in st.session_state and 'df_cov_final' in st.session_state:
        d_req = st.session_state['df_intra_final']
        d_sch = st.session_state['df_cov_final'].reindex(d_req.index).fillna(0).astype(int)
        common = [c for c in d_sch.columns if c in d_req.columns]
        if common:
            st.subheader(f"⚖️ Efficiency Gap (Schedules - Required): {lang}")
            df_net = d_sch[common] - d_req[common] #
            st.dataframe(df_net.style.applymap(color_net_staffing), use_container_width=True) #
    else: st.info("يرجى اختيار اللغة ورفع الملفات أولاً")
