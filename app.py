import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time

st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# --- دالة التلوين ---
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

tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity", "⏰ Intraday", "🗓️ Scheduling", "⚖️ Net Staffing"])

# --- TAB 1: Capacity (الشكل القديم اللي بتحبه) ---
with tab1:
    with st.sidebar:
        st.header("⚙️ Global Settings")
        d_range = st.date_input("Select Date Range", [date(2026, 2, 1), date(2026, 2, 28)])
        start_date, end_date = d_range[0], (d_range[1] if len(d_range) > 1 else d_range[0])
        main_file = st.file_uploader("Upload Data.xlsx (Capacity)", type=["xlsx"])

    if main_file:
        df_all_data = pd.read_excel(main_file, sheet_name=0) # قراءة البيانات من Sheet1
        # اختيار اللغة للكابستي فقط هنا
        cap_lang = st.selectbox("🌍 Select Language for Capacity Analysis", df_all_data.iloc[:, 0].unique())
        
        row = df_all_data[df_all_data.iloc[:, 0] == cap_lang].iloc[0]
        working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
        base_hours = working_days * 8
        
        target_hrs = float(row.iloc[1])
        actual_hc = float(row.iloc[2])
        shrink_p = float(row.iloc[3]) / 100 if float(row.iloc[3]) > 1 else float(row.iloc[3])
        req_hc = np.ceil(target_hrs / (base_hours * (1 - shrink_p))) if base_hours > 0 else 0
        
        st.markdown(f"### 📋 Detailed Capacity for **{cap_lang}**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Target Hours", f"{int(target_hrs)}h")
        c2.metric("Required HC", int(req_hc))
        c3.metric("HC Variance", int(actual_hc - req_hc), delta=int(actual_hc - req_hc))

# --- TAB 2: Intraday (مكان فلتر اللغة الأساسي للعمليات) ---
with tab2:
    st.subheader("Half-Hour Interval Requirements")
    intra_file = st.file_uploader("Upload Required.xlsx", type=["xlsx"])
    if intra_file:
        # فلتر اللغة اللي هيتحكم في السكادول والنيت ستافينج
        xls = pd.ExcelFile(intra_file)
        languages = [s for s in xls.sheet_names if "Sheet" not in s]
        sel_lang = st.selectbox("🎯 Select Language (App Filter)", languages, key="main_lang_filter")
        st.session_state['active_lang'] = sel_lang # حفظ اللغة للتابات التالية
        
        df_raw = pd.read_excel(intra_file, sheet_name=sel_lang, header=None)
        if not df_raw.empty:
            new_cols = ["Intervals"] + [pd.to_datetime(d).strftime('%Y-%m-%d') for d in df_raw.iloc[0, 1:]]
            df_intra = df_raw.drop(0).copy()
            df_intra.columns = new_cols
            df_intra['Intervals'] = df_intra['Intervals'].apply(format_time_index)
            st.session_state['df_intra'] = df_intra.set_index('Intervals').apply(pd.to_numeric, errors='coerce').fillna(0).round(0).astype(int)
            st.success(f"Data Loaded for {sel_lang}")
            st.dataframe(st.session_state['df_intra'], use_container_width=True)

# --- TAB 3: Scheduling (بيسمع من فلتر الانترا داي) ---
with tab3:
    sched_file = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"])
    lang = st.session_state.get('active_lang')
    if sched_file and lang:
        st.info(f"Showing Schedules for: **{lang}** (Based on Intraday Filter)")
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
        except: st.error(f"Sheet '{lang}' not found in Schedule file.")

# --- TAB 4: Net Staffing (المقارنة النهائية) ---
with tab4:
    lang = st.session_state.get('active_lang')
    if 'df_intra' in st.session_state and 'df_cov' in st.session_state:
        st.subheader(f"⚖️ Net Staffing: {lang}")
        d_intra = st.session_state['df_intra']
        d_cov = st.session_state['df_cov'].reindex(d_intra.index).fillna(0).astype(int)
        common_cols = [c for c in d_cov.columns if c in d_intra.columns]
        if common_cols:
            df_net = d_cov[common_cols] - d_intra[common_cols]
            st.dataframe(df_net.style.applymap(color_net_staffing), use_container_width=True)
