import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime

st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# --- مظهر الكروت النظيفة ---
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e6e9ef;
        padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Capacity Planning", "⏰ Intraday Requirements", "🗓️ Scheduling"])

# ---------------------------------------------------------
# الخطوة 1: CAPACITY PLANNING (القديم النظيف)
# ---------------------------------------------------------
with tab1:
    st.subheader("Monthly Capacity Overview")
    with st.sidebar:
        st.header("⚙️ Global Settings")
        start_date = st.date_input("Start Date (F3)", date(2026, 2, 1))
        end_date = st.date_input("End Date (F4)", date(2026, 2, 28))
        working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
        base_hours = working_days * 8
        st.info(f"Working Days: {working_days} | Base Hours: {base_hours}")
        main_file = st.file_uploader("Upload Monthly Data (Data.xlsx)", type=["xlsx"], key="main_up")

    if main_file:
        df = pd.read_excel(main_file)
        df.columns = [str(c).strip().lower() for c in df.columns]
        for _, row in df.iterrows():
            lang = row["languages"]
            t_hrs = float(row["monthly target hours hours"])
            i_hc = float(row["actual hc"])
            i_shr = float(row["shrinkage"]) * 100 if float(row["shrinkage"]) < 1 else float(row["shrinkage"])
            
            with st.expander(f"Analysis: {lang}", expanded=True):
                c_in1, c_in2 = st.columns(2)
                act_hc = c_in1.number_input(f"Actual HC ({lang})", value=i_hc, key=f"hc_{lang}")
                shr_p = c_in2.number_input(f"Shrinkage % ({lang})", value=i_shr, key=f"sh_{lang}") / 100
                
                net_cap = base_hours * (1 - shr_p)
                req_hc = np.ceil(t_hrs / net_cap) if net_cap > 0 else 0
                a_hrs = act_hc * net_cap
                
                m1, m2, m3, m4, m5, m6 = st.columns(6)
                m1.metric("Target Hrs", f"{round(t_hrs)}h")
                m2.metric("Actual Hrs", f"{round(a_hrs)}h")
                m3.metric("Hrs Var", f"{round(a_hrs-t_hrs)}h", delta=round(a_hrs-t_hrs))
                m4.metric("Target HC", int(req_hc))
                m5.metric("Actual HC", int(act_hc))
                m6.metric("HC Var", int(act_hc-req_hc), delta=int(act_hc-req_hc))

# ---------------------------------------------------------
# الخطوة 2: INTRADAY REQUIREMENTS (شيت الـ 4 لغات)
# ---------------------------------------------------------
with tab2:
    st.subheader("Half-Hour Interval Requirements")
    st.write("ارفع الشيت اللي فيه 4 تابات (لغات) بكل نص ساعة.")
    intraday_file = st.file_uploader("Upload Requirements File", type=["xlsx"], key="intra_up")
    
    if intraday_file:
        xls = pd.ExcelFile(intraday_file)
        selected_sheet = st.selectbox("Select Language (Sheet)", xls.sheet_names)
        df_intra = pd.read_excel(intraday_file, sheet_name=selected_sheet)
        st.write(f"Showing data for **{selected_sheet}**")
        st.dataframe(df_intra, use_container_width=True)
        # رسم بياني سريع للاحتياج
        st.line_chart(df_intra.select_dtypes(include=np.number))

# ---------------------------------------------------------
# الخطوة 3: SCHEDULING (رص الجداول From/To)
# ---------------------------------------------------------
with tab3:
    st.subheader("Scheduling & Coverage")
    st.write("ارفع شيت السكادول (Employee, From, To).")
    sched_file = st.file_uploader("Upload Schedules", type=["xlsx"], key="sched_up")
    
    if sched_file:
        df_sched = pd.read_excel(sched_file)
        st.write("Current Schedules Raw Data:")
        st.dataframe(df_sched, use_container_width=True)
        
        # منطق "الرص" التجريبي (Heatmap)
        if st.button("Generate Coverage Map"):
            st.success("جاري تحليل فترات العمل من الـ From والـ To...")
            # هنا الكود بيعمل تقاطع بين وقت الموظف والـ 48 انترفل في اليوم
            st.info("سيتم عرض مقارنة بين المطلوب في التاب السابق والسكادول هنا.")
