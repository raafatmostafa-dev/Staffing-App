import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time
import os
import base64

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="WFM Professional Suite", layout="wide", initial_sidebar_state="collapsed")

# إخفاء الشريط الجانبي تماماً عبر CSS لجعل الواجهة احترافية
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="stSidebarNav"] {
        display: none;
    }
    .stApp { background-color: #FFFFFF; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; color: #1E3A8A !important; }
    .main-header { font-size: 1.2rem; font-weight: bold; color: #1E3A8A; border-bottom: 2px solid #EEEEEE; padding-bottom: 10px; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def save_file(uploaded_file, name):
    with open(name, "wb") as f:
        f.write(uploaded_file.getbuffer())

def color_net_staffing(val):
    try:
        if val < 0: return 'background-color: #ffcccc; color: #900000; font-weight: bold'
        if val > 0: return 'background-color: #ccffcc; color: #006600'
    except: pass
    return ''

def format_time_index(t):
    if isinstance(t, (time, datetime)): return t.strftime('%H:%M')
    try: return pd.to_datetime(str(t)).strftime('%H:%M')
    except: return str(t)

# --- 2. نظام تسجيل الدخول ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center; margin-top: 50px;'>🔒 WFM Secure Access</h2>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if user == "Raafat Mostafa" and pw == "Rr#01010353831":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ بيانات الدخول غير صحيحة")
    st.stop()

# --- 3. محتوى التطبيق بعد الدخول ---

# إنشاء التبويبات
tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity Dashboard", "🎯 Resource Requirements", "🗓️ Scheduling", "⚖️ Net Staffing"])

with tab1:
    # قسم الإعدادات (بديل الشريط الجانبي)
    with st.expander("⚙️ Configuration & Data Upload", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            d_range = st.date_input("Analysis Period", [date(2026, 4, 1), date(2026, 4, 30)])
        with c2:
            up_main = st.file_uploader("Upload Data.xlsx", type=["xlsx"])
            if up_main: save_file(up_main, "data_last.xlsx")
        with c3:
            up_intra = st.file_uploader("Upload Requirements.xlsx", type=["xlsx"])
            if up_intra: save_file(up_intra, "intra_last.xlsx")
            up_sched = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"])
            if up_sched: save_file(up_sched, "sched_last.xlsx")
            if st.button("Logout", use_container_width=True):
                st.session_state["authenticated"] = False
                st.rerun()

    start_date = d_range[0]
    end_date = d_range[1] if len(d_range) > 1 else d_range[0]

    if os.path.exists("data_last.xlsx"):
        df_all = pd.read_excel("data_last.xlsx", sheet_name=0)
        # حساب أيام العمل الفعلي بين تاريخين
        working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
        base_hrs_per_person = working_days * 8
        st.markdown('<p class="main-header">🌍 Global Fleet Capacity Analysis</p>', unsafe_allow_html=True)

        for _, row in df_all.iterrows():
            lang_name = str(row.iloc[0])
            target_workload_hrs = float(row.iloc[1])
            actual_hc_count = float(row.iloc[2])
            shrink_val = float(row.iloc[3])
            shrink_p = shrink_val / 100 if shrink_val > 1 else shrink_val 
            
            actual_available_hrs = (actual_hc_count * base_hrs_per_person) * (1 - shrink_p)
            hrs_variance = actual_available_hrs - target_workload_hrs
            req_hc = np.ceil(target_workload_hrs / (base_hrs_per_person * (1 - shrink_p))) if base_hrs_per_person > 0 else 0
            hc_variance = actual_hc_count - req_hc

            with st.expander(f"🚩 Language: {lang_name.upper()}", expanded=True):
                m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
                m1.metric("Tgt Hrs", f"{int(target_workload_hrs):,}h")
                m2.metric("Act Hrs", f"{int(actual_available_hrs):,}h")
                m3.metric("Hrs Var", f"{int(hrs_variance):,}h", delta=int(hrs_variance))
                m4.metric("Shrink %", f"{shrink_p*100:.1f}%")
                m5.metric("Req HC", f"{int(req_hc)}")
                m6.metric("Act HC", f"{int(actual_hc_count)}")
                m7.metric("HC Gap", f"{int(hc_variance)}", delta=int(hc_variance))

with tab2:
    if os.path.exists("intra_last.xlsx"):
        xls = pd.ExcelFile("intra_last.xlsx")
        avail_langs = [s for s in xls.sheet_names if "Sheet" not in s]
        op_lang = st.selectbox("🎯 Select Language", avail_langs, key="op_filter")
        st.session_state['active_lang'] = op_lang
        
        df_raw = pd.read_excel("intra_last.xlsx", sheet_name=op_lang, header=None)
        if not df_raw.empty:
            new_cols = ["Intervals"] + [pd.to_datetime(d).strftime('%Y-%m-%d') for d in df_raw.iloc[0, 1:]]
            df_intra = df_raw.drop(0).copy()
            df_intra.columns = new_cols
            df_intra['Intervals'] = df_intra['Intervals'].apply(format_time_index)
            final_df_intra = df_intra.set_index('Intervals').apply(pd.to_numeric, errors='coerce').fillna(0).round(0).astype(int)
            st.session_state['df_intra'] = final_df_intra
            st.dataframe(final_df_intra, use_container_width=True)

with tab3:
    lang = st.session_state.get('active_lang')
    if os.path.exists("sched_last.xlsx") and lang:
        st.subheader(f"🗓️ Staff Coverage Calculation: {lang}")
        try:
            # قراءة الملف بدون تحديد أسماء أعمدة في البداية لضمان المرونة
            df_s = pd.read_excel("sched_last.xlsx", sheet_name=lang)
            
            # محاولة تحديد الأعمدة الصحيحة بناءً على الترتيب في صورتك
            # نفترض: التاريخ (0)، الاسم (1)، البداية (2)، النهاية (3)
            df_s.columns = ['Day', 'Name', 'Start Time', 'End Time'] + list(df_s.columns[4:])
            
            df_s['Day'] = pd.to_datetime(df_s['Day']).dt.date
            
            intervals = pd.date_range("00:00", "23:30", freq="30min").strftime('%H:%M').tolist()
            target_dates = pd.date_range(start_date, end_date).date.tolist()
            df_coverage = pd.DataFrame(0, index=intervals, columns=[d.strftime('%Y-%m-%d') for d in target_dates])

            for _, r in df_s.iterrows():
                if pd.isna(r['Day']): continue
                curr_day = r['Day']
                
                try:
                    # تحويل القيم إلى نصوص وتنظيفها
                    st_raw = str(r['Start Time']).strip().upper()
                    en_raw = str(r['End Time']).strip().upper()
                    
                    # تخطي أيام الإجازات
                    if any(x in st_raw for x in ['OFF', 'NAN', '-', '']): continue
                    
                    # معالجة الوقت بصيغة AM/PM أو 24 ساعة
                    start_t = pd.to_datetime(st_raw).time()
                    end_t = pd.to_datetime(en_raw).time()
                    
                    s_min = start_t.hour * 60 + start_t.minute
                    e_min = end_t.hour * 60 + end_t.minute

                    for slot in intervals:
                        slot_dt = datetime.strptime(slot, '%H:%M').time()
                        sl_min = slot_dt.hour * 60 + slot_dt.minute
                        day_str = curr_day.strftime('%Y-%m-%d')
                        
                        # منطق الحساب
                        if s_min < e_min: # شيفت عادي
                            if s_min <= sl_min < e_min:
                                if day_str in df_coverage.columns: df_coverage.at[slot, day_str] += 1
                        else: # شيفت ليلي
                            if sl_min >= s_min: 
                                if day_str in df_coverage.columns: df_coverage.at[slot, day_str] += 1
                            elif sl_min < e_min:
                                next_day_str = (curr_day + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                                if next_day_str in df_coverage.columns: df_coverage.at[slot, next_day_str] += 1
                except:
                    continue # تخطي أي سطر فيه خطأ في تنسيق الوقت

            st.session_state['df_cov'] = df_coverage
            st.dataframe(df_coverage, use_container_width=True)
            
        except Exception as e:
            st.error(f"⚠️ تأكد من ترتيب الأعمدة في الإكسيل (التاريخ، الاسم، البداية، النهاية). الخطأ: {e}")
with tab4:
    lang = st.session_state.get('active_lang')
    if 'df_intra' in st.session_state and 'df_cov' in st.session_state:
        st.subheader(f"⚖️ Efficiency Analysis: {lang}")
        d_intra = st.session_state['df_intra']
        # إعادة مواءمة جدول التغطية مع جدول المتطلبات
        d_cov = st.session_state['df_cov'].reindex(d_intra.index).fillna(0).astype(int)
        common_cols = [c for c in d_cov.columns if c in d_intra.columns]
        if common_cols:
            df_net = d_cov[common_cols] - d_intra[common_cols]
            st.dataframe(df_net.style.map(color_net_staffing), use_container_width=True)
    else:
        st.info("الرجاء رفع البيانات أولاً واختيار لغة من تبويب Resource Requirements.")
