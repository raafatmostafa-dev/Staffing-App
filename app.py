import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime

st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# --- دالة التلوين لتابة المقارنة ---
def color_net_staffing(val):
    if isinstance(val, (int, float)):
        if val < 0: return 'background-color: #ffcccc; color: #900000; font-weight: bold'
        if val > 0: return 'background-color: #ccffcc; color: #006600'
    return ''

# --- التبويبات ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity", "⏰ Intraday", "🗓️ Scheduling", "⚖️ Net Staffing"])

# ---------------------------------------------------------
# TAB 1: CAPACITY PLANNING
# ---------------------------------------------------------
with tab1:
    st.sidebar.header("⚙️ Global Settings")
    start_date = st.sidebar.date_input("Start Date", date(2026, 2, 1))
    end_date = st.sidebar.date_input("End Date", date(2026, 2, 28))
    main_file = st.file_uploader("Upload Data.xlsx", type=["xlsx"])
    if main_file:
        xls = pd.ExcelFile(main_file)
        sel_lang = st.selectbox("Select Language", xls.sheet_names)
        df_cap = pd.read_excel(main_file, sheet_name=sel_lang)
        st.success(f"Language {sel_lang} Loaded")

# ---------------------------------------------------------
# TAB 2: INTRADAY (إصلاح الـ Intervals والتواريخ)
# ---------------------------------------------------------
with tab2:
    st.subheader("Half-Hour Interval Requirements")
    intra_file = st.file_uploader("Upload Required.xlsx", type=["xlsx"])
    if intra_file:
        xls_int = pd.ExcelFile(intra_file)
        lang_int = st.selectbox("Select Language (Intraday)", xls_int.sheet_names)
        df_raw = pd.read_excel(intra_file, sheet_name=lang_int, header=None)
        
        # 1. تنظيف التواريخ في الهيدر
        h_row = df_raw.iloc[0].values
        new_cols = ["Intervals"]
        for v in h_row[1:]:
            try: new_cols.append(pd.to_datetime(v).strftime('%Y-%m-%d'))
            except: new_cols.append(str(v))
        
        df_intra = df_raw.drop(0).copy()
        df_intra.columns = new_cols
        
        # 2. تحويل الـ Intervals لنص صافي (HH:MM) لضمان الظهور
        df_intra['Intervals'] = pd.to_datetime(df_intra['Intervals'], errors='coerce').dt.strftime('%H:%M')
        df_intra = df_intra.dropna(subset=['Intervals'])
        
        # تخزين البيانات في الـ session
        st.session_state['df_intra'] = df_intra.set_index('Intervals').fillna(0)
        st.write("### Required Data Table")
        st.dataframe(st.session_state['df_intra'], use_container_width=True)

# ---------------------------------------------------------
# TAB 3: SCHEDULING (تحويل المواعيد لأرقام تغطية)
# ---------------------------------------------------------
with tab3:
    st.subheader("Employee Staffing Schedules")
    sched_file = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"])
    if sched_file:
        xls_sch = pd.ExcelFile(sched_file)
        lang_sch = st.selectbox("Select Language (Schedule)", xls_sch.sheet_names)
        df_s = pd.read_excel(sched_file, sheet_name=lang_sch)
        
        # إنشاء قائمة Intervals موحدة (نصية)
        intervals = pd.date_range("00:00", "23:30", freq="30min").strftime('%H:%M').tolist()
        df_s['Day'] = pd.to_datetime(df_s['Day'], errors='coerce')
        u_days = sorted(df_s['Day'].dropna().unique())
        
        cov_dict = {"Intervals": intervals}
        for d in u_days:
            d_str = pd.to_datetime(d).strftime('%Y-%m-%d')
            day_df = df_s[df_s['Day'] == d]
            counts = []
            for slot in intervals:
                slot_t = datetime.strptime(slot, '%H:%M').time()
                c = 0
                for _, r in day_df.iterrows():
                    try:
                        if str(r['Start Time']).upper() == 'OFF': continue
                        st_t = pd.to_datetime(str(r['Start Time'])).time()
                        en_t = pd.to_datetime(str(r['End Time'])).time()
                        if st_t <= slot_t < en_t: c += 1
                    except: continue
                counts.append(c)
            cov_dict[d_str] = counts
            
        st.session_state['df_cov'] = pd.DataFrame(cov_dict).set_index('Intervals')
        st.write("### Scheduled Coverage Table")
        st.dataframe(st.session_state['df_cov'], use_container_width=True)

# ---------------------------------------------------------
# TAB 4: NET STAFFING (المقارنة والطرح)
# ---------------------------------------------------------
with tab4:
    st.subheader("Net Staffing Analysis (Gap)")
    if 'df_intra' in st.session_state and 'df_cov' in st.session_state:
        d_intra = st.session_state['df_intra']
        d_cov = st.session_state['df_cov']
        
        # إيجاد الأيام المشتركة بين الملفين
        common_days = [c for c in d_cov.columns if c in d_intra.columns]
        
        if common_days:
            # توحيد الـ Index بين الجدولين لضمان الطرح الصحيح
            d_cov_aligned = d_cov.reindex(d_intra.index).fillna(0)
            
            # طرح (المتاح - المطلوب)
            df_net = d_cov_aligned[common_cols].astype(float) - d_intra[common_cols].astype(float)
            
            st.write("🔴 أحمر = عجز | 🟢 أخضر = زيادة")
            st.dataframe(df_net.style.applymap(color_net_staffing), use_container_width=True)
        else:
            st.warning("⚠️ لا توجد تواريخ متطابقة بين الملفين المرفوعين.")
    else:
        st.info("💡 يرجى رفع الملفات في التابات السابقة أولاً.")
