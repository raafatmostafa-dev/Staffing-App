import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime

# إعدادات الصفحة
st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# --- تحسين الواجهة CSS (للكروت والتبويبات) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e6e9ef;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        background-color: #f0f2f6; 
        border-radius: 5px; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- نظام التبويبات الثلاثة ---
tab1, tab2, tab3 = st.tabs(["📊 Capacity Planning", "⏰ Intraday Requirements", "🗓️ Scheduling"])

# ---------------------------------------------------------
# الخطوة 1: CAPACITY PLANNING (Monthly Data)
# ---------------------------------------------------------
with tab1:
    st.subheader("Monthly Capacity Analysis")
    
    with st.sidebar:
        st.header("⚙️ Global Settings")
        # إعدادات التاريخ لحساب أيام العمل (F3, F4)
        start_date = st.date_input("Start Date (F3)", date(2026, 2, 1))
        end_date = st.date_input("End Date (F4)", date(2026, 2, 28))
        
        # حساب أيام العمل NETWORKDAYS
        start_np = np.datetime64(start_date)
        end_np = np.datetime64(end_date) + np.timedelta64(1, 'D')
        working_days = np.busday_count(start_np, end_np)
        base_hours = working_days * 8
        
        st.info(f"📅 Working Days: {working_days}")
        st.info(f"⏳ Base Hours/Month: {base_hours}")
        st.divider()
        main_file = st.file_uploader("Upload Data.xlsx", type=["xlsx"], key="main_up")

    if main_file:
        try:
            df = pd.read_excel(main_file)
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            # ربط الأعمدة من ملفك
            col_lang = "languages"
            col_target_hrs = "monthly target hours hours"
            col_actual_hc = "actual hc"
            col_shr = "shrinkage"

            for _, row in df.iterrows():
                lang = row[col_lang]
                t_hrs = float(row[col_target_hrs])
                i_hc = float(row[col_actual_hc])
                # تحويل الشرينكيدج لنسبة مئوية
                raw_shr = float(row[col_shr])
                i_shr = raw_shr * 100 if raw_shr < 1 else raw_shr

                with st.expander(f"Analysis for: {lang}", expanded=True):
                    c_in1, c_in2 = st.columns(2)
                    act_hc = c_in1.number_input(f"Actual HC ({lang})", value=i_hc, key=f"hc_{lang}")
                    shr_p = c_in2.number_input(f"Shrinkage % ({lang})", value=i_shr, key=f"sh_{lang}") / 100
                    
                    # معادلات الحساب
                    n_cap = base_hours * (1 - shr_p)
                    req_hc = np.ceil(t_hrs / n_cap) if n_cap > 0 else 0
                    a_hrs = act_hc * n_cap
                    
                    # عرض الـ 6 أرقام المطلوبة
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Target Hours", f"{round(t_hrs)}h")
                    m2.metric("Actual Hours", f"{round(a_hrs)}h")
                    m3.metric("Hrs Variance", f"{round(a_hrs - t_hrs)}h", delta=round(a_hrs - t_hrs))
                    
                    m4, m5, m6 = st.columns(3)
                    m4.metric("Target HC", int(req_hc))
                    m5.metric("Actual HC", int(act_hc))
                    m6.metric("HC Variance", int(act_hc - req_hc), delta=int(act_hc - req_hc))
        except Exception as e:
            st.error(f"Error in Capacity Tab: {e}")

# ---------------------------------------------------------
# الخطوة 2: INTRADAY REQUIREMENTS (Interval Analysis)
# ---------------------------------------------------------
with tab2:
    st.subheader("Half-Hour Interval Requirements")
    st.write("ارفع الشيت اللي فيه 4 تابات (لغات) بكل نص ساعة.")
    
    intraday_file = st.file_uploader("Upload Requirements File", type=["xlsx"], key="intra_up")
    
    if intraday_file:
        try:
            xls = pd.ExcelFile(intraday_file)
            selected_sheet = st.selectbox("Select Language (Sheet)", xls.sheet_names)
            df_intra = pd.read_excel(intraday_file, sheet_name=selected_sheet)
            
            # --- تنظيف الوقت والتاريخ (عشان ما يظهرش 1970) ---
            if not df_intra.empty:
                # تحويل العمود الأول (غالباً الوقت) وكل ما يتعلق بالوقت لنص مقروء
                for col in df_intra.columns:
                    # لو العمود فيه وقت (Interval)
                    if 'interval' in str(col).lower() or col == df_intra.columns[0]:
                        df_intra[col] = pd.to_datetime(df_intra[col], errors='coerce').dt.strftime('%H:%M')
                    # لو العمود فيه تاريخ
                    elif isinstance(df_intra[col].iloc[0], (datetime, date)):
                        df_intra[col] = pd.to_datetime(df_intra[col], errors='coerce').dt.strftime('%Y-%m-%d')
            
            st.write(f"Showing data for: **{selected_sheet}**")
            st.dataframe(df_intra.fillna(""), use_container_width=True)
            
            # رسم بياني توضيحي للاحتياج
            numeric_cols = df_intra.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0
