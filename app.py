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

tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity Dashboard", "⏰ Intraday", "🗓️ Scheduling", "⚖️ Net Staffing"])

# --- TAB 1: Capacity Dashboard (عرض الكل تحت بعض) ---
with tab1:
    with st.sidebar:
        st.header("⚙️ Configuration")
        d_range = st.date_input("Analysis Period", [date(2026, 2, 1), date(2026, 2, 28)])
        start_date, end_date = d_range[0], (d_range[1] if len(d_range) > 1 else d_range[0])
        main_file = st.file_uploader("Upload Data.xlsx", type=["xlsx"])

    if main_file:
        df_all = pd.read_excel(main_file, sheet_name=0) # قراءة الشيت الأساسي
        
        # حسابات الوقت العامة
        working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
        base_hrs_per_person = working_days * 8

        st.title("🌍 Global Fleet Capacity Dashboard")
        st.info(f"Analysis for {working_days} working days ({base_hrs_per_person} base hours/FTE)")

        # لوب (Loop) عشان نعرض كل لغة في كارت لوحدها تحت بعض
        for index, row in df_all.iterrows():
            lang_name = str(row.iloc[0])
            target_workload_hrs = float(row.iloc[1])
            actual_hc_count = float(row.iloc[2])
            shrink_p = float(row.iloc[3]) / 100 if float(row.iloc[3]) > 1 else float(row.iloc[3])

            # الحسابات مع اعتبار الشرينكيدج في الاتنين
            # 1. تحليل الساعات
            actual_available_hrs = (actual_hc_count * base_hrs_per_person) * (1 - shrink_p)
            hrs_variance = actual_available_hrs - target_workload_hrs
            
            # 2. تحليل الموظفين
            req_hc = np.ceil(target_workload_hrs / (base_hrs_per_person * (1 - shrink_p))) if base_hrs_per_person > 0 else 0
            hc_variance = actual_hc_count - req_hc

            # تصميم الكارت الاحترافي لكل لغة
            with st.expander(f"🚩 Language: {lang_name.upper()}", expanded=True):
                # عرض الساعات
                st.markdown(f"#### ⏱️ Hours Performance (Shrinkage: {shrink_p*100:.1f}%)")
                h1, h2, h3 = st.columns(3)
                h1.metric("Target Workload", f"{int(target_workload_hrs):,}h")
                h2.metric("Actual Available", f"{int(actual_available_hrs):,}h")
                h3.metric("Hours Variance", f"{int(hrs_variance):,}h", delta=int(hrs_variance))

                # عرض الموظفين
                st.markdown(f"#### 👥 Headcount Requirements")
                c1, c2, c3 = st.columns(3)
                c1.metric("Required FTEs", f"{int(req_hc)} HC")
                c2.metric("Actual FTEs", f"{int(actual_hc_count)} HC")
                c3.metric("Staffing Gap", f"{int(hc_variance)} HC", delta=int(hc_variance))
            
            st.markdown("---") # فاصل بين كل لغة والتانية

# --- بقية التابات مرتبطة بفلتر اللغة في الانتراداي لضمان عدم ظهور None ---
with tab2:
    # سيتم وضع فلتر اللغة هنا للتحكم في الجداول التفصيلية
    pass
    st.subheader("⏰ Interval Requirements")
    intra_file = st.file_uploader("Upload Required.xlsx", type=["xlsx"])
    if intra_file:
        xls = pd.ExcelFile(intra_file)
        avail_langs = [s for s in xls.sheet_names if "Sheet" not in s]
        # فلتر اللغة الموحد للعمليات
        op_lang = st.selectbox("🎯 Operational Language", avail_langs, key="op_filter")
        st.session_state['active_lang'] = op_lang
        
        df_raw = pd.read_excel(intra_file, sheet_name=op_lang, header=None)
        if not df_raw.empty:
            new_cols = ["Intervals"] + [pd.to_datetime(d).strftime('%Y-%m-%d') for d in df_raw.iloc[0, 1:]]
            df_intra = df_raw.drop(0).copy()
            df_intra.columns = new_cols
            df_intra['Intervals'] = df_intra['Intervals'].apply(format_time_index)
            st.session_state['df_intra'] = df_intra.set_index('Intervals').apply(pd.to_numeric, errors='coerce').fillna(0).round(0).astype(int)
            st.dataframe(st.session_state['df_intra'], use_container_width=True)

with tab3:
    sched_file = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"])
    lang = st.session_state.get('active_lang')
    if sched_file and lang:
        st.subheader(f"🗓️ Coverage for {lang}")
        # ... (كود حساب التغطية كما في النسخ السابقة لضمان الدقة)
        # سيتم استخدام 'lang' المأخوذة من تابة الانترا داي أوتوماتيكياً

with tab4:
    if 'df_intra' in st.session_state and 'df_cov' in st.session_state:
        st.subheader(f"⚖️ Net Staffing Analysis: {st.session_state.get('active_lang')}")
        # المقارنة النهائية بدون None
        d_intra = st.session_state['df_intra']
        d_cov = st.session_state['df_cov'].reindex(d_intra.index).fillna(0).astype(int)
        common_cols = [c for c in d_cov.columns if c in d_intra.columns]
        if common_cols:
            df_net = d_cov[common_cols] - d_intra[common_cols]
            st.dataframe(df_net.style.applymap(color_net_staffing), use_container_width=True)

