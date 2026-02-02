import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time

st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# --- دالة التلوين للأرقام الصحيحة ---
def color_net_staffing(val):
    try:
        if val < 0: return 'background-color: #ffcccc; color: #900000; font-weight: bold'
        if val > 0: return 'background-color: #ccffcc; color: #006600'
    except: pass
    return ''

# --- توحيد تنسيق الوقت (حل مشكلة الـ None) ---
def format_time_index(t):
    if isinstance(t, (time, datetime)): return t.strftime('%H:%M')
    try: return pd.to_datetime(str(t)).strftime('%H:%M')
    except: return str(t)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity", "⏰ Intraday", "🗓️ Scheduling", "⚖️ Net Staffing"])

# --- TAB 1: Capacity (الرجوع للشكل القديم ومعالجة شيت البيانات) ---
with tab1:
    with st.sidebar:
        st.header("⚙️ Global Settings")
        d_range = st.date_input("Select Date Range", [date(2026, 2, 1), date(2026, 2, 28)])
        start_date, end_date = d_range[0], (d_range[1] if len(d_range) > 1 else d_range[0])
        
        main_file = st.file_uploader("Upload Data.xlsx (Capacity)", type=["xlsx"])

    if main_file:
        # قراءة الشيت الأساسي (Sheet1)
        df_all_data = pd.read_excel(main_file, sheet_name=0) 
        languages = df_all_data.iloc[:, 0].unique().tolist()
        
        sel_lang = st.selectbox("🌍 Select Language", languages)
        st.session_state['active_lang'] = sel_lang # تثبيت اللغة للأبلكيشن كله
        
        # فلترة البيانات بناءً على اللغة المختارة
        lang_data = df_all_data[df_all_data.iloc[:, 0] == sel_lang].iloc[0]
        
        # حساب الساعات (المعادلة الأصلية)
        working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
        base_hours = working_days * 8
        
        # جلب القيم من الأعمدة (Target, Actual, Shrinkage)
        target_hrs = float(lang_data.iloc[1])
        actual_hc = float(lang_data.iloc[2])
        shrink_val = float(lang_data.iloc[3])
        shrink_p = shrink_val / 100 if shrink_val > 1 else shrink_val
        
        # الحسبة
        req_hc = np.ceil(target_hrs / (base_hours * (1 - shrink_p))) if base_hours > 0 else 0
        
        st.markdown(f"### 📊 Capacity Results for **{sel_lang}**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Target Hours", f"{int(target_hrs)}h")
        c2.metric("Required HC", int(req_hc))
        c3.metric("HC Variance", int(actual_hc - req_hc), delta=int(actual_hc - req_hc))

# --- TAB 2: Intraday (قراءة النص ساعة بدقة) ---
with tab2:
    intra_file = st.file_uploader("Upload Required.xlsx", type=["xlsx"])
    if intra_file:
        # بيفتح أوتوماتيك على الشيت اللي اسمه زي اللغة المختارة
        lang = st.session_state.get('active_lang', "Arabic")
        try:
            df_raw = pd.read_excel(intra_file, sheet_name=lang, header=None)
            new_cols = ["Intervals"] + [pd.to_datetime(d).strftime('%Y-%m-%d') for d in df_raw.iloc[0, 1:]]
            df_intra = df_raw.drop(0).copy()
            df_intra.columns = new_cols
            df_intra['Intervals'] = df_intra['Intervals'].apply(format_time_index)
            
            final_intra = df_intra.set_index('Intervals').apply(pd.to_numeric, errors='coerce').fillna(0).round(0).astype(int)
            st.session_state['df_intra'] = final_intra
            st.dataframe(final_intra, use_container_width=True)
        except:
            st.error(f"Sheet '{lang}' not found in Required.xlsx")

# --- TAB 3: Scheduling ---
with tab3:
    sched_file = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"])
    if sched_file:
        lang_s = st.session_state.get('active_lang', "Arabic")
        try:
            df_s = pd.read_excel(sched_file, sheet_name=lang_s)
            intervals = pd.date_range("00:00", "23:30", freq="30min").strftime('%H:%M').tolist()
            df_s['Day'] = pd.to_datetime(df_s['Day'], errors='coerce')
            target_dates = pd.date_range(start_date, end_date).strftime('%Y-%m-%d').tolist()
            
            cov_dict = {"Intervals": intervals}
            for d_str in target_dates:
                day_df = df_s[df_s['Day'].dt.strftime('%Y-%m-%d') == d_str]
                counts = []
                for slot in intervals:
                    slot_t = datetime.strptime(slot, '%H:%M').time()
                    c = 0
                    for _, r in day_df.iterrows():
                        try:
                            st_v = str(r['Start Time']).strip().upper()
                            if st_v in ['OFF', 'NAN', '-', '']: continue
                            st_t = pd.to_datetime(st_v).time()
                            en_t = pd.to_datetime(str(r['End Time'])).time()
                            if (st_t <= slot_t < en_t) if st_t < en_t else (slot_t >= st_t or slot_t < en_t): c += 1
                        except: continue
                    counts.append(c)
                cov_dict[d_str] = counts
            
            final_cov = pd.DataFrame(cov_dict).set_index('Intervals').astype(int)
            st.session_state['df_cov'] = final_cov
            st.dataframe(final_cov, use_container_width=True)
        except:
            st.error(f"Sheet '{lang_s}' not found in Schedules.xlsx")

# --- TAB 4: Net Staffing (المقارنة بدون None) ---
with tab4:
    if 'df_intra' in st.session_state and 'df_cov' in st.session_state:
        d_intra = st.session_state['df_intra']
        d_cov =
