import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime

st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# --- دالة التلوين لتابة المقارنة ---
def color_net_staffing(val):
    if isinstance(val, (int, float)):
        if val < 0: return 'background-color: #ffcccc; color: #900000; font-weight: bold' # أحمر للعجز
        if val > 0: return 'background-color: #ccffcc; color: #006600' # أخضر للزيادة
    return ''

# --- واجهة التبويبات الأربعة ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Capacity Planning", 
    "⏰ Intraday Requirements", 
    "🗓️ Scheduling", 
    "⚖️ Net Staffing"
])

# ---------------------------------------------------------
# TAB 1: CAPACITY PLANNING (السحب من تابات اللغة)
# ---------------------------------------------------------
with tab1:
    st.subheader("Monthly Capacity Analysis")
    with st.sidebar:
        st.header("⚙️ Global Settings")
        start_date = st.date_input("Start Date", date(2026, 2, 1))
        end_date = st.date_input("End Date", date(2026, 2, 28))
        working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
        base_hours = working_days * 8
        st.info(f"📅 Working Days: {working_days} | ⏳ Base Hours: {base_hours}")
        main_file = st.file_uploader("Upload Data.xlsx", type=["xlsx"], key="cap_up")

    if main_file:
        xls_cap = pd.ExcelFile(main_file)
        sel_lang = st.selectbox("Select Language (Sheet)", xls_cap.sheet_names, key="cap_lang")
        df_cap = pd.read_excel(main_file, sheet_name=sel_lang)
        df_cap.columns = [str(c).strip().lower() for c in df_cap.columns]
        
        col_t = next((c for c in df_cap.columns if 'target' in c), None)
        col_a = next((c for c in df_cap.columns if 'actual' in c), None)
        col_s = next((c for c in df_cap.columns if 'shrink' in c), None)

        if all([col_t, col_a, col_s]):
            row = df_cap.iloc[0]
            shrink_val = float(row[col_s])
            shrink_p = shrink_val if shrink_val < 1 else shrink_val / 100
            n_cap = base_hours * (1 - shrink_p)
            req_hc = np.ceil(float(row[col_t]) / n_cap) if n_cap > 0 else 0
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Target Hours", f"{int(row[col_t])}h")
            c2.metric("Required HC", int(req_hc))
            c3.metric("HC Variance", int(float(row[col_a]) - req_hc), delta=int(float(row[col_a]) - req_hc))

# ---------------------------------------------------------
# TAB 2: INTRADAY REQUIREMENTS (تنظيف الهيدر والتواريخ)
# ---------------------------------------------------------
with tab2:
    st.subheader("Half-Hour Interval Requirements")
    intraday_file = st.file_uploader("Upload Required.xlsx", type=["xlsx"], key="int_up")
    if intraday_file:
        xls_int = pd.ExcelFile(intraday_file)
        lang_int = st.selectbox("Select Language (Intraday)", xls_int.sheet_names, key="int_lang")
        df_raw = pd.read_excel(intraday_file, sheet_name=lang_int, header=None)
        
        # معالجة التواريخ في الهيدر
        h_row = df_raw.iloc[0].values
        new_cols = ["Intervals"]
        for v in h_row[1:]:
            try: new_cols.append(pd.to_datetime(v).strftime('%Y-%m-%d'))
            except: new_cols.append(str(v))
        
        df_intra = df_raw.drop(0).copy()
        df_intra.columns = new_cols
        # إزالة تاريخ 1970 من الوقت
        df_intra['Intervals'] = pd.to_datetime(df_intra['Intervals'], errors='coerce').dt.strftime('%H:%M')
        df_intra = df_intra.dropna(subset=['Intervals']).set_index('Intervals')
        
        st.session_state['df_intra'] = df_intra.fillna(0)
        st.dataframe(st.session_state['df_intra'], use_container_width=True)

# ---------------------------------------------------------
# TAB 3: SCHEDULING (تحويل المواعيد النصية إلى أرقام تغطية)
# ---------------------------------------------------------
with tab3:
    st.subheader("Staffing Coverage Calculation")
    sched_file = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"], key="sch_up")
    if sched_file:
        xls_sch = pd.ExcelFile(sched_file)
        lang_sch = st.selectbox("Select Language (Schedule)", xls_sch.sheet_names, key="sch_lang")
        df_s = pd.read_excel(sched_file, sheet_name=lang_sch)
        
        if not df_s.empty:
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
                            # تجاهل الـ OFF والتعامل مع النصوص
                            s_val = str(r['Start Time']).strip().upper()
                            if s_val in ['OFF', 'NAN']: continue
                            st_t = pd.to_datetime(s_val).time()
                            en_t = pd.to_datetime(str(r['End Time'])).time()
                            if st_t <= slot_t < en_t: c += 1
                        except: continue
                    counts.append(c)
                cov_dict[d_str] = counts
            
            st.session_state['df_cov'] = pd.DataFrame(cov_dict).set_index('Intervals')
            st.dataframe(st.session_state['df_cov'], use_container_width=True)

# ---------------------------------------------------------
# TAB 4: NET STAFFING (المقارنة وحل مشكلة AssertionError)
# ---------------------------------------------------------
with tab4:
    st.subheader("Net Staffing Analysis (Gap)")
    if 'df_intra' in st.session_state and 'df_cov' in st.session_state:
        d_intra = st.session_state['df_intra']
        d_cov = st.session_state['df_cov']
        
        common_cols = [c for c in d_cov.columns if c in d_intra.columns]
        
        if common_cols:
            # توحيد الصفوف (Intervals) قسرياً لحل AssertionError
            d_cov_aligned = d_cov.reindex(d_intra.index).fillna(0)
            
            # طرح (المتاح - المطلوب)
            df_net = d_cov_aligned[common_cols].astype(float) - d_intra[common_cols].astype(float)
            
            st.write("### 🔴 Red = Understaffed | 🟢 Green = Overstaffed")
            st.dataframe(df_net.style.applymap(color_net_staffing), use_container_width=True)
        else:
            st.warning("⚠️ No matching dates found between the two files.")
    else:
        st.info("💡 Please upload both Required and Schedule files first.")
