import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time

st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# --- CSS لتصغير الخط وتحسين المظهر الاحترافي ---
st.markdown("""
    <style>
    /* تصغير خط المايتريكس ليتناسب مع العرض الجديد */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
    }
    .main-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- دالة التلوين لجدول الـ Net Staffing ---
def color_net_staffing(val):
    try:
        if val < 0: return 'background-color: #ffcccc; color: #900000; font-weight: bold'
        if val > 0: return 'background-color: #ccffcc; color: #006600'
    except: pass
    return ''

# --- توحيد تنسيق الوقت ---
def format_time_index(t):
    if isinstance(t, (time, datetime)): return t.strftime('%H:%M')
    try: return pd.to_datetime(str(t)).strftime('%H:%M')
    except: return str(t)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity Dashboard", "⏰ Intraday", "🗓️ Scheduling", "⚖️ Net Staffing"])

# --- TAB 1: Capacity Dashboard (إضافة خانة الشرينكيدج) ---
with tab1:
    with st.sidebar:
        st.header("⚙️ Configuration")
        d_range = st.date_input("Analysis Period", [date(2026, 2, 1), date(2026, 2, 28)])
        start_date, end_date = d_range[0], (d_range[1] if len(d_range) > 1 else d_range[0])
        main_file = st.file_uploader("Upload Data.xlsx (Master)", type=["xlsx"])

    if main_file:
        df_all = pd.read_excel(main_file, sheet_name=0)
        working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
        base_hrs_per_person = working_days * 8

        st.markdown('<p class="main-header">🌍 Global Fleet Capacity Analysis (All Languages)</p>', unsafe_allow_html=True)

        for _, row in df_all.iterrows():
            lang_name = str(row.iloc[0])
            target_workload_hrs = float(row.iloc[1])
            actual_hc_count = float(row.iloc[2])
            shrink_val = float(row.iloc[3])
            # معالجة النسبة المئوية
            shrink_p = shrink_val / 100 if shrink_val > 1 else shrink_val 

            # الحسابات الأساسية (مع اعتبار الشرينكيدج في الاتنين)
            actual_available_hrs = (actual_hc_count * base_hrs_per_person) * (1 - shrink_p)
            hrs_variance = actual_available_hrs - target_workload_hrs
            req_hc = np.ceil(target_workload_hrs / (base_hrs_per_person * (1 - shrink_p))) if base_hrs_per_person > 0 else 0
            hc_variance = actual_hc_count - req_hc

            # عرض الكارت مع خانة الشرينكيدج الجديدة
            with st.expander(f"🚩 Language: {lang_name.upper()}", expanded=True):
                c1, c2, c3, c4, c5, c6, c7 = st.columns(7) # تم زيادة الأعمدة لـ 7
                c1.metric("Tgt Hrs", f"{int(target_workload_hrs):,}h")
                c2.metric("Act Hrs", f"{int(actual_available_hrs):,}h")
                c3.metric("Hrs Var", f"{int(hrs_variance):,}h", delta=int(hrs_variance))
                c4.metric("Shrink %", f"{shrink_p*100:.1f}%") # خانة الشرينكيدج المطلوبة
                c5.metric("Req HC", f"{int(req_hc)}")
                c6.metric("Act HC", f"{int(actual_hc_count)}")
                c7.metric("HC Gap", f"{int(hc_variance)}", delta=int(hc_variance))
        st.divider()

# --- TAB 2: Intraday (الفلتر القائد) ---
with tab2:
    st.subheader("⏰ Interval Requirements")
    intra_file = st.file_uploader("Upload Required.xlsx", type=["xlsx"])
    if intra_file:
        xls = pd.ExcelFile(intra_file)
        avail_langs = [s for s in xls.sheet_names if "Sheet" not in s]
        op_lang = st.selectbox("🎯 Select Language (Master Filter)", avail_langs, key="op_filter")
        st.session_state['active_lang'] = op_lang # ربط اللغة للتابات التالية
        
        df_raw = pd.read_excel(intra_file, sheet_name=op_lang, header=None)
        if not df_raw.empty:
            new_cols = ["Intervals"] + [pd.to_datetime(d).strftime('%Y-%m-%d') for d in df_raw.iloc[0, 1:]]
            df_intra = df_raw.drop(0).copy()
            df_intra.columns = new_cols
            df_intra['Intervals'] = df_intra['Intervals'].apply(format_time_index)
            st.session_state['df_intra'] = df_intra.set_index('Intervals').apply(pd.to_numeric, errors='coerce').fillna(0).round(0).astype(int)
            st.dataframe(st.session_state['df_intra'], use_container_width=True)

# --- TAB 3: Scheduling ---
with tab3:
    sched_file = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"])
    lang = st.session_state.get('active_lang')
    if sched_file and lang:
        st.subheader(f"🗓️ Staff Coverage: {lang}")
        try:
            df_s = pd.read_excel(sched_file, sheet_name=lang)
            intervals = pd.date_range("00:00", "23:30", freq="30min").strftime('%H:%M').tolist()
            df_s['Day'] = pd.to_datetime(df_s['Day'], errors='coerce')
            target_dates = pd.date_range(start_date, end_date).strftime('%Y-%m-%d').tolist()
            
            cov_dict = {"Intervals": intervals}
            for d_str in target_dates:
                day_df = df_s[df_s['Day'].dt.strftime('%Y-%m-%d') == d_str]
                counts = [0] * len(intervals)
                for i, slot in enumerate(intervals):
                    slot_t = datetime.strptime(slot, '%H:%M').time()
                    for _, r in day_df.iterrows():
                        try:
                            st_v = str(r['Start Time']).strip().upper()
                            if st_v in ['OFF', 'NAN', '-', '']: continue
                            st_t, en_t = pd.to_datetime(st_v).time(), pd.to_datetime(str(r['End Time'])).time()
                            if (st_t <= slot_t < en_t) if st_t < en_t else (slot_t >= st_t or slot_t < en_t): counts[i] += 1
                        except: continue
                cov_dict[d_str] = counts
            st.session_state['df_cov'] = pd.DataFrame(cov_dict).set_index('Intervals').astype(int)
            st.dataframe(st.session_state['df_cov'], use_container_width=True)
        except: st.error(f"Sheet '{lang}' not found in Schedules.")

# --- TAB 4: Net Staffing ---
with tab4:
    lang = st.session_state.get('active_lang')
    if 'df_intra' in st.session_state and 'df_cov' in st.session_state:
        st.subheader(f"⚖️ Efficiency Analysis: {lang}")
        d_intra = st.session_state['df_intra']
        # إصلاح مشكلة None بضمان مطابقة الفهرس
        d_cov = st.session_state['df_cov'].reindex(d_intra.index).fillna(0).astype(int)
        
        common_cols = [c for c in d_cov.columns if c in d_intra.columns]
        if common_cols:
            df_net = d_cov[common_cols] - d_intra[common_cols]
            st.dataframe(df_net.style.applymap(color_net_staffing), use_container_width=True)
    else:
        st.warning("Please upload Intraday and Schedule files to see the gap analysis.")
