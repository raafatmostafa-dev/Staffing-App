import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime

# إعدادات الصفحة
st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# --- تحسين الواجهة CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e6e9ef;
        padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f0f2f6; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Capacity Planning", "⏰ Intraday Requirements", "🗓️ Scheduling"])

# --- TAB 1: CAPACITY PLANNING ---
with tab1:
    st.subheader("Monthly Capacity Analysis")
    with st.sidebar:
        st.header("⚙️ Global Settings")
        start_date = st.date_input("Start Date", date(2026, 2, 1))
        end_date = st.date_input("End Date", date(2026, 2, 28))
        working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
        base_hours = working_days * 8
        st.info(f"📅 Working Days: {working_days} | ⏳ Base Hours: {base_hours}")
        main_file = st.file_uploader("Upload Data.xlsx", type=["xlsx"], key="main_up")

    if main_file:
        df = pd.read_excel(main_file)
        df.columns = [str(c).strip().lower() for c in df.columns]
        for _, row in df.iterrows():
            lang = row["languages"]
            with st.expander(f"Analysis for: {lang}", expanded=True):
                # الحسابات (Target vs Actual) كما في طلبك الأول
                n_cap = base_hours * (1 - (float(row["shrinkage"])))
                req_hc = np.ceil(float(row["monthly target hours hours"]) / n_cap) if n_cap > 0 else 0
                st.metric("Required HC", int(req_hc), delta=int(float(row["actual hc"]) - req_hc))

# --- TAB 2: INTRADAY REQUIREMENTS ---
with tab2:
    st.subheader("Half-Hour Interval Requirements")
    intraday_file = st.file_uploader("Upload Required.xlsx", type=["xlsx"], key="intra_up")
    if intraday_file:
        xls_intra = pd.ExcelFile(intraday_file)
        sel_lang_intra = st.selectbox("Select Language (Requirements)", xls_intra.sheet_names)
        df_raw = pd.read_excel(intraday_file, sheet_name=sel_lang_intra, header=None)
        
        # معالجة الهيدر والتواريخ لتجنب التكرار
        header_row = df_raw.iloc[0].values
        new_cols = ["Intervals"] + [pd.to_datetime(d).strftime('%Y-%m-%d') if pd.notnull(d) and i>0 else str(d) for i, d in enumerate(header_row[1:], 1)]
        df_intra = df_raw.drop(0).copy()
        df_intra.columns = new_cols
        df_intra['Intervals'] = pd.to_datetime(df_intra['Intervals'], errors='coerce').dt.strftime('%H:%M')
        st.dataframe(df_intra.fillna(0), use_container_width=True)

# --- TAB 3: SCHEDULING (المعدلة لسحب الـ 4 تابات) ---
with tab3:
    st.subheader("Employee Staffing Schedules")
    st.write("ارفع شيت السكادول الذي يحتوي على تابات اللغات (Haitian Creole, Arabic, etc.)")
    
    sched_file = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"], key="sched_up")
    
    if sched_file:
        try:
            # قراءة ملف السكادول ومعرفة أسماء التابات (اللغات)
            xls_sched = pd.ExcelFile(sched_file)
            selected_lang_sched = st.selectbox("Select Language to View Schedule", xls_sched.sheet_names)
            
            # قراءة الداتا الخاصة باللغة المختارة
            df_sched = pd.read_excel(sched_file, sheet_name=selected_lang_sched)
            
            # تنظيف البيانات وتنسيق الوقت
            if not df_sched.empty:
                # تحويل عمود التاريخ لشكل مقروء
                if 'Day' in df_sched.columns:
                    df_sched['Day'] = pd.to_datetime(df_sched['Day'], errors='ignore').dt.strftime('%Y-%m-%d')
                
                # تحويل وقت البداية والنهاية لنص نظيف (HH:MM AM/PM)
                for time_col in ['Start Time', 'End Time']:
                    if time_col in df_sched.columns:
                        df_sched[time_col] = pd.to_datetime(df_sched[time_col], errors='coerce').dt.strftime('%I:%M %p')
            
            st.success(f"Showing Schedules for: **{selected_lang_sched}**")
            st.dataframe(df_sched.fillna("-"), use_container_width=True)
            
            # زر إضافي للتحليل مستقبلاً
            if st.button("Calculate Coverage Gap"):
                st.info("سأقوم في الخطوة القادمة بمقارنة هذه المواعيد مع احتياجات الـ Intraday.")
                
        except Exception as e:
            st.error(f"Error loading Schedules: {e}")
