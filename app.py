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
        start_date = st.date_input("Start Date (F3)", date(2026, 2, 1))
        end_date = st.date_input("End Date (F4)", date(2026, 2, 28))
        
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
            
            for _, row in df.iterrows():
                lang = row["languages"]
                t_hrs = float(row["monthly target hours hours"])
                i_hc = float(row["actual hc"])
                raw_shr = float(row["shrinkage"])
                i_shr = raw_shr * 100 if raw_shr < 1 else raw_shr

                with st.expander(f"Analysis for: {lang}", expanded=True):
                    c_in1, c_in2 = st.columns(2)
                    act_hc = c_in1.number_input(f"Actual HC ({lang})", value=i_hc, key=f"hc_{lang}")
                    shr_p = c_in2.number_input(f"Shrinkage % ({lang})", value=i_shr, key=f"sh_{lang}") / 100
                    
                    n_cap = base_hours * (1 - shr_p)
                    req_hc = np.ceil(t_hrs / n_cap) if n_cap > 0 else 0
                    a_hrs = act_hc * n_cap
                    
                    m1, m2, m3, m4, m5, m6 = st.columns(6)
                    m1.metric("Target Hrs", f"{round(t_hrs)}h")
                    m2.metric("Actual Hrs", f"{round(a_hrs)}h")
                    m3.metric("Hrs Var", f"{round(a_hrs - t_hrs)}h", delta=round(a_hrs - t_hrs))
                    m4.metric("Target HC", int(req_hc))
                    m5.metric("Actual HC", int(act_hc))
                    m6.metric("HC Var", int(act_hc - req_hc), delta=int(act_hc - req_hc))
        except Exception as e:
            st.error(f"Error in Capacity: {e}")

# ---------------------------------------------------------
# الخطوة 2: INTRADAY REQUIREMENTS (قراءة التواريخ من الهيدر)
# ---------------------------------------------------------
with tab2:
    st.subheader("Half-Hour Interval Requirements")
    intraday_file = st.file_uploader("Upload Required.xlsx", type=["xlsx"], key="intra_up")
    
    if intraday_file:
        try:
            xls = pd.ExcelFile(intraday_file)
            selected_sheet = st.selectbox("Select Language (Sheet)", xls.sheet_names)
            
            # قراءة الشيت بالكامل بدون هيدر للتحكم فيه
            df_raw = pd.read_excel(intraday_file, sheet_name=selected_sheet, header=None)
            
            if not df_raw.empty:
                # 1. استخراج التواريخ من أول صف (Row 0)
                header_row = df_raw.iloc[0].values
                new_columns = []
                
                for i, val in enumerate(header_row):
                    if i == 0:
                        new_columns.append("Intervals")
                    else:
                        try:
                            # تحويل التواريخ لشكل نظيف YYYY-MM-DD
                            clean_date = pd.to_datetime(val).strftime('%Y-%m-%d')
                            new_columns.append(clean_date)
                        except:
                            new_columns.append(str(val))
                
                # 2. تعيين الهيدر الجديد وحذف أول صف
                df_intra = df_raw.copy()
                df_intra.columns = new_columns
                df_intra = df_intra.drop(0).reset_index(drop=True)
                
                # 3. تنظيف الوقت (Intervals) من تاريخ 1970
                df_intra['Intervals'] = pd.to_datetime(df_intra['Intervals'], errors='coerce').dt.strftime('%H:%M')
                
                st.write(f"Showing data for: **{selected_sheet}**")
                # عرض الجدول بشكل نهائي
                st.dataframe(df_intra.fillna(0), use_container_width=True)
                
                # رسم بياني لأول يوم كمثال
                numeric_cols = df_intra.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    st.line_chart(df_intra.set_index('Intervals')[numeric_cols[0]])

        except Exception as e:
            st.error(f"Error in Intraday: {e}")

# ---------------------------------------------------------
# الخطوة 3: SCHEDULING (Shift Management)
# ---------------------------------------------------------
with tab3:
    st.subheader("Staffing Schedules")
    sched_file = st.file_uploader("Upload Schedule File", type=["xlsx"], key="sched_up")
    
    if sched_file:
        try:
            df_sched = pd.read_excel(sched_file)
            st.dataframe(df_sched, use_container_width=True)
            if st.button("Analyze Coverage"):
                st.success("Analysis Complete!")
        except Exception as e:
            st.error(f"Error in Scheduling: {e}")
