import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime

st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# --- تحسين الواجهة CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e6e9ef;
        padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Capacity Planning", "⏰ Intraday Requirements", "🗓️ Scheduling"])

# --- TAB 1: CAPACITY PLANNING (حل مشكلة KeyError) ---
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
        try:
            df = pd.read_excel(main_file)
            # تنظيف أسماء الأعمدة: مسح المسافات وتحويلها لحروف صغيرة
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            # محاولة ذكية لإيجاد الأعمدة حتى لو اسمها اتغير
            col_lang = next((c for c in df.columns if 'lang' in c), df.columns[0])
            col_target = next((c for c in df.columns if 'target' in c), df.columns[1])
            col_actual = next((c for c in df.columns if 'actual' in c), df.columns[2])
            col_shrink = next((c for c in df.columns if 'shrink' in c), df.columns[3])

            for _, row in df.iterrows():
                lang = row[col_lang]
                with st.expander(f"Analysis for: {lang}", expanded=True):
                    # حساب الـ Required HC بناءً على بياناتك
                    shrink_val = float(row[col_shrink])
                    shrink_p = shrink_val if shrink_val < 1 else shrink_val / 100
                    n_cap = base_hours * (1 - shrink_p)
                    
                    target_hrs = float(row[col_target])
                    actual_hc = float(row[col_actual])
                    req_hc = np.ceil(target_hrs / n_cap) if n_cap > 0 else 0
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Target Hours", f"{round(target_hrs)}h")
                    m2.metric("Required HC", int(req_hc))
                    m3.metric("HC Gap", int(actual_hc - req_hc), delta=int(actual_hc - req_hc))
        except Exception as e:
            st.error(f"Make sure columns follow: Language, Target Hours, Actual HC, Shrinkage. (Error: {e})")

# --- TAB 2: INTRADAY REQUIREMENTS ---
with tab2:
    st.subheader("Half-Hour Interval Requirements")
    intraday_file = st.file_uploader("Upload Required.xlsx", type=["xlsx"], key="intra_up")
    if intraday_file:
        try:
            xls_intra = pd.ExcelFile(intraday_file)
            sel_lang_intra = st.selectbox("Select Language (Requirements)", xls_intra.sheet_names)
            df_raw = pd.read_excel(intraday_file, sheet_name=sel_lang_intra, header=None)
            
            # تنسيق الهيدر والتواريخ
            header_row = df_raw.iloc[0].values
            new_cols = ["Intervals"]
            for i, val in enumerate(header_row[1:], 1):
                try: new_cols.append(pd.to_datetime(val).strftime('%Y-%m-%d'))
                except: new_cols.append(str(val))
            
            df_intra = df_raw.drop(0).copy()
            df_intra.columns = new_cols
            df_intra['Intervals'] = pd.to_datetime(df_intra['Intervals'], errors='coerce').dt.strftime('%H:%M')
            st.dataframe(df_intra.fillna(0), use_container_width=True)
        except Exception as e:
            st.error(f"Error in Intraday: {e}")

# --- TAB 3: SCHEDULING ---
with tab3:
    st.subheader("Employee Staffing Schedules")
    sched_file = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"], key="sched_up")
    
    if sched_file:
        try:
            xls_sched = pd.ExcelFile(sched_file)
            selected_lang_sched = st.selectbox("Select Language (Schedule)", xls_sched.sheet_names)
            df_sched = pd.read_excel(sched_file, sheet_name=selected_lang_sched)
            
            # تنظيف السكادول
            if not df_sched.empty:
                if 'Day' in df_sched.columns:
                    df_sched['Day'] = pd.to_datetime(df_sched['Day'], errors='coerce').dt.strftime('%Y-%m-%d')
                for c in ['Start Time', 'End Time']:
                    if c in df_sched.columns:
                        df_sched[c] = pd.to_datetime(df_sched[c], errors='coerce').dt.strftime('%I:%M %p')
            
            st.dataframe(df_sched.fillna("-"), use_container_width=True)
        except Exception as e:
            st.error(f"Error in Schedules: {e}")
