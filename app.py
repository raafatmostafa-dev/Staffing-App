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
    main_file = st.file_uploader("Upload Data.xlsx", type=["xlsx"], key="cap_up")
    if main_file:
        xls = pd.ExcelFile(main_file)
        sel_lang = st.selectbox("Select Language", xls.sheet_names)
        st.success(f"Language {sel_lang} Loaded")

# ---------------------------------------------------------
# TAB 2: INTRADAY (إصلاح مشكلة الشرطات "-" والبيانات المختفية)
# ---------------------------------------------------------
with tab2:
    st.subheader("Half-Hour Interval Requirements")
    intra_file = st.file_uploader("Upload Required.xlsx", type=["xlsx"], key="int_up")
    if intra_file:
        xls_int = pd.ExcelFile(intra_file)
        lang_int = st.selectbox("Select Language (Intraday)", xls_int.sheet_names)
        # قراءة الداتا مع اعتبار الشرطة NaN عشان نقدر نحولها لصفر
        df_raw = pd.read_excel(intra_file, sheet_name=lang_int, header=None, na_values=['-'])
        
        # معالجة الهيدر (التواريخ)
        h_row = df_raw.iloc[0].values
        new_cols = ["Intervals"]
        for v in h_row[1:]:
            try: new_cols.append(pd.to_datetime(v).strftime('%Y-%m-%d'))
            except: new_cols.append(str(v))
        
        df_intra = df_raw.drop(0).copy()
        df_intra.columns = new_cols
        
        # تنظيف الوقت وإجبار البيانات تبقى أرقام
        df_intra['Intervals'] = pd.to_datetime(df_intra['Intervals'], errors='coerce').dt.strftime('%H:%M')
        df_intra = df_intra.dropna(subset=['Intervals'])
        
        # تحويل كل الخلايا لأرقام (الشرطات هتبقى 0)
        final_intra = df_intra.set_index('Intervals').apply(pd.to_numeric, errors='coerce').fillna(0)
        st.session_state['df_intra'] = final_intra
        
        st.write("✅ **Data Loaded Successfully:**")
        st.dataframe(st.session_state['df_intra'], use_container_width=True)

# ---------------------------------------------------------
# TAB 3: SCHEDULING (تحويل المواعيد لأرقام)
# ---------------------------------------------------------
with tab3:
    st.subheader("Employee Staffing Schedules")
    sched_file = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"], key="sch_up")
    if sched_file:
        xls_sch = pd.ExcelFile(sched_file)
        lang_sch = st.selectbox("Select Language (Schedule)", xls_sch.sheet_names)
        df_s = pd.read_excel(sched_file, sheet_name=lang_sch)
        
        # قائمة فترات نصية HH:MM
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
                        if str(r['Start Time']).upper() in ['OFF', 'NAN']: continue
                        st_t = pd.to_datetime(str(r['Start Time'])).time()
                        en_t = pd.to_datetime(str(r['End Time'])).time()
                        if st_t <= slot_t < en_t: c += 1
                    except: continue
                counts.append(c)
            cov_dict[d_str] = counts
            
        st.session_state['df_cov'] = pd.DataFrame(cov_dict).set_index('Intervals')
        st.dataframe(st.session_state['df_cov'], use_container_width=True)

# ---------------------------------------------------------
# TAB 4: NET STAFFING (المقارنة النهائية)
# ---------------------------------------------------------
with tab4:
    st.subheader("Net Staffing Analysis (Gap)")
    if 'df_intra' in st.session_state and 'df_cov' in st.session_state:
        d_intra = st.session_state['df_intra']
        d_cov = st.session_state['df_cov']
        
        # إيجاد الأيام المشتركة وتوحيد الجداول
        common_cols = [c for c in d_cov.columns if c in d_intra.columns]
        
        if common_cols:
            d_cov_aligned = d_cov.reindex(d_intra.index).fillna(0)
            df_net = d_cov_aligned[common_cols] - d_intra[common_cols]
            
            st.write("🔴 أحمر = عجز (نقص موظفين) | 🟢 أخضر = زيادة")
            st.dataframe(df_net.style.applymap(color_net_staffing), use_container_width=True)
            
            csv = df_net.to_csv().encode('utf-8')
            st.download_button("📥 Download Report", csv, "gap_analysis.csv", "text/csv")
        else:
            st.warning("⚠️ No matching dates found.")
    else:
        st.info("💡 Please upload Required and Schedule files first.")
