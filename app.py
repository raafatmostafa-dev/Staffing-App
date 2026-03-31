import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time
import os

# --- 1. إعدادات الصفحة والتصميم الفاخر المطور ---
st.set_page_config(page_title="WFM Professional Suite", layout="wide", initial_sidebar_state="collapsed")

# تصميم CSS متطور مع الخلفية الجديدة وتأثيرات الظل
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    /* تغيير خلفية التطبيق للون الرمادي المزرق الاحترافي */
    .stApp {
        background-color: #F0F2F6;
    }

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    /* إخفاء القوائم الجانبية والعناصر الافتراضية لزيادة المساحة */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"] { display: none; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* تصميم التبويبات (Tabs) لتبرز فوق الخلفية */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
        color: #64748B;
        border: 1px solid #E2E8F0;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A !important;
        color: white !important;
        border: 1px solid #1E3A8A !important;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.2);
    }

    /* تحسين شكل كروت البيانات (Metrics) وتبريزها بظل خفيف */
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #E2E8F0;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -1px;
        margin-bottom: 30px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# دالة حفظ الملفات المرفوعة
def save_file(uploaded_file, name):
    with open(name, "wb") as f:
        f.write(uploaded_file.getbuffer())

# دالة التلوين الشرطي لجدول الفرق (Delta) - لا تحتاج مكتبات خارجية
def color_net_staffing(val):
    try:
        if val < 0: return 'background-color: #FFF1F2; color: #BE123C; font-weight: bold; border: 0.5px solid #FECDD3'
        if val > 0: return 'background-color: #F0FDF4; color: #15803D; border: 0.5px solid #DCFCE7'
    except: pass
    return ''

# دالة بسيطة لتلوين الجداول العادية بدون matplotlib
def simple_style(val):
    return 'background-color: white; color: #1E293B;'

# --- 2. نظام تسجيل الدخول ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("""
            <div style='background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); border: 1px solid #F1F5F9;'>
                <h2 style='text-align: center; color: #1E3A8A; font-weight: 800;'>WFM Suite</h2>
                <p style='text-align: center; color: #64748B; margin-bottom: 30px;'>Enter credentials to access the portal</p>
            </div>
        """, unsafe_allow_html=True)
        user = st.text_input("Username", placeholder="e.g. Raafat Mostafa")
        pw = st.text_input("Password", type="password", placeholder="••••••••")
        if st.button("Authorize Access", use_container_width=True):
            if user == "Raafat Mostafa" and pw == "Rr#01010353831":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("🔒 Unauthorized Credentials")
    st.stop()

# --- 3. التطبيق الرئيسي ---
st.markdown('<h1 class="main-header">Workforce Management Dashboard</h1>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Executive Summary", "🎯 Requirements", "🗓️ Schedule View", "⚖️ Delta Analysis"])

with tab1:
    with st.expander("🛠️ Control Panel & Data Ingestion", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            d_range = st.date_input("Analysis Window", [date(2026, 4, 1), date(2026, 4, 30)])
        with c2:
            up_main = st.file_uploader("Upload Core Data (Excel)", type=["xlsx"])
            if up_main: save_file(up_main, "data_last.xlsx")
        with c3:
            up_intra = st.file_uploader("Upload Intrady Requirements", type=["xlsx"])
            if up_intra: save_file(up_intra, "intra_last.xlsx")
            up_sched = st.file_uploader("Upload Master Schedules", type=["xlsx"])
            if up_sched: save_file(up_sched, "sched_last.xlsx")

    start_date = d_range[0]
    end_date = d_range[1] if len(d_range) > 1 else d_range[0]

    if os.path.exists("data_last.xlsx"):
        df_all = pd.read_excel("data_last.xlsx")
        working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
        base_hrs = working_days * 8
        
        for _, row in df_all.iterrows():
            lang, target_hrs, act_hc, shrink = str(row.iloc[0]), float(row.iloc[1]), float(row.iloc[2]), float(row.iloc[3])
            shrink_p = shrink/100 if shrink > 1 else shrink
            
            avail_hrs = (act_hc * base_hrs) * (1 - shrink_p)
            req_hc = np.ceil(target_hrs / (base_hrs * (1 - shrink_p))) if base_hrs > 0 else 0
            
            st.markdown(f"""
                <div style='background: #1E3A8A; padding: 10px 20px; border-radius: 10px 10px 0 0; color: white; margin-top: 20px;'>
                    <span style='font-weight: 800;'>🌍 LANGUAGE GROUP: {lang.upper()}</span>
                </div>
            """, unsafe_allow_html=True)
            
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Target Load", f"{int(target_hrs):,}h")
            m2.metric("Supply Cap", f"{int(avail_hrs):,}h")
            m3.metric("Shrinkage", f"{shrink_p*100:.1f}%")
            m4.metric("Required HC", int(req_hc))
            m5.metric("Active HC", int(act_hc))
            m6.metric("HC Gap", int(act_hc - req_hc), delta=int(act_hc - req_hc))

with tab2:
    if os.path.exists("intra_last.xlsx"):
        xls = pd.ExcelFile("intra_last.xlsx")
        avail_langs = [s for s in xls.sheet_names if "Sheet" not in s]
        op_lang = st.selectbox("Active Viewport:", avail_langs)
        st.session_state['active_lang'] = op_lang
        
        df_raw = pd.read_excel("intra_last.xlsx", sheet_name=op_lang, header=None)
        if not df_raw.empty:
            new_cols = ["Intervals"] + [pd.to_datetime(d).strftime('%Y-%m-%d') for d in df_raw.iloc[0, 1:]]
            df_intra = df_raw.drop(0).copy()
            df_intra.columns = new_cols
            df_intra.set_index("Intervals", inplace=True)
            st.session_state['df_intra'] = df_intra.apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
            st.dataframe(st.session_state['df_intra'], use_container_width=True)

with tab3:
    lang = st.session_state.get('active_lang')
    if os.path.exists("sched_last.xlsx") and lang:
        try:
            df_s = pd.read_excel("sched_last.xlsx", sheet_name=lang)
            df_s['Day'] = pd.to_datetime(df_s['Day']).dt.date
            intervals = pd.date_range("00:00", "23:30", freq="30min").strftime('%H:%M').tolist()
            df_cov = pd.DataFrame(0, index=intervals, columns=[pd.to_datetime(c).strftime('%Y-%m-%d') for c in st.session_state['df_intra'].columns])
            
            for _, r in df_s.iterrows():
                if pd.isna(r['Day']): continue
                st_t = pd.to_datetime(str(r['Start Time'])).time()
                en_t = pd.to_datetime(str(r['End Time'])).time()
                for slot in intervals:
                    sl_t = datetime.strptime(slot, '%H:%M').time()
                    d_str = r['Day'].strftime('%Y-%m-%d')
                    if d_str in df_cov.columns:
                        if st_t < en_t:
                            if st_t <= sl_t < en_t: df_cov.at[slot, d_str] += 1
                        else:
                            if sl_t >= st_t or sl_t < en_t:
                                target = d_str if sl_t >= st_t else (r['Day'] + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                                if target in df_cov.columns: df_cov.at[slot, target] += 1
            st.session_state['df_cov'] = df_cov
            st.dataframe(df_cov, use_container_width=True)
        except Exception as e: st.error(f"Error: {e}")

with tab4:
    if 'df_intra' in st.session_state and 'df_cov' in st.session_state:
        d_intra = st.session_state['df_intra']
        d_cov = st.session_state['df_cov'].reindex(d_intra.index).fillna(0).astype(int)
        df_net = d_cov - d_intra
        st.dataframe(df_net.style.applymap(color_net_staffing), use_container_width=True)
