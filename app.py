import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time
import os
import base64

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# دالة تحويل الصورة لخلفية (لشاشة الدخول فقط)
def set_bg_image(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            img_data = f.read()
        b64_encoded = base64.b64encode(img_data).decode()
        style = f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{b64_encoded}");
            background-size: cover;
            background-position: center 40%;
            background-attachment: fixed;
        }}
        </style>
        """
        st.markdown(style, unsafe_allow_html=True)

# دالة حفظ الملفات للثبات
def save_file(uploaded_file, name):
    with open(name, "wb") as f:
        f.write(uploaded_file.getbuffer())

# --- 2. نظام تسجيل الدخول ---
def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    # وضع الخلفية في شاشة الـ Login فقط
    set_bg_image("background.jpg")

    st.markdown("<h2 style='color: white; text-shadow: 2px 2px 4px #000000; text-align: center;'>🔒 WFM Secure Access</h2>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("""
            <style>
            div[data-testid="stVerticalBlock"] > div:has(input) {
                background-color: rgba(255, 255, 255, 0.9);
                padding: 30px;
                border-radius: 15px;
            }
            </style>
            """, unsafe_allow_html=True)
        
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if user == "Raafat Mostafa" and pw == "Rr#01010353831": 
                st.session_state["authenticated"] = True
                st.rerun() 
            else:
                st.error("❌ بيانات الدخول غير صحيحة")
    return False

# --- 3. تشغيل التطبيق بعد الدخول ---
if check_auth():
    # كود الـ CSS (الدارك مود للعمود الجانبي فقط واللايت مود للباقي)
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            background-color: #1E1E1E !important;
        }
        [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label {
            color: #00FFCC !important;
        }
        [data-testid="stSidebar"] .stButton button {
            background-color: #333;
            color: white;
            border: 1px solid #00FFCC;
        }
        .stApp {
            background-color: #FFFFFF;
        }
        [data-testid="stMetricValue"] { font-size: 1.5rem !important; color: #1E3A8A !important; }
        [data-testid="stMetricLabel"] { font-size: 0.85rem !important; color: #444 !important; }
        .main-header { 
            font-size: 1.2rem; 
            font-weight: bold; 
            color: #1E3A8A; 
            margin-bottom: 20px;
            border-bottom: 2px solid #EEEEEE;
            padding-bottom: 10px;
        }
        </style>
        """, unsafe_allow_html=True)

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

    # تعديل مسمى التابة هنا
# أضفنا key="v3_resource" لإجبار الواجهة على التحديث
tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity Dashboard", "🎯 Resource Requirements", "🗓️ Scheduling", "⚖️ Net Staffing"], key="v3_resource") 
with tab1:
        with st.sidebar:
            st.header("⚙️ Configuration")
            d_range = st.date_input("Analysis Period", [date(2026, 2, 1), date(2026, 2, 28)])
            start_date, end_date = d_range[0], (d_range[1] if len(d_range) > 1 else d_range[0])
            
            up_main = st.file_uploader("Upload Data.xlsx", type=["xlsx"])
            if up_main: save_file(up_main, "data_last.xlsx")
            
            # تعديل مسمى الرفع هنا ليتناسب مع القسم الجديد
            up_intra = st.file_uploader("Upload Resource Requirements.xlsx", type=["xlsx"])
            if up_intra: save_file(up_intra, "intra_last.xlsx")
            
            up_sched = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"])
            if up_sched: save_file(up_sched, "sched_last.xlsx")
            
            if st.button("Logout"):
                st.session_state["authenticated"] = False
                st.rerun()

        if os.path.exists("data_last.xlsx"):
            df_all = pd.read_excel("data_last.xlsx", sheet_name=0)
            working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
            base_hrs_per_person = working_days * 8
            st.markdown('<p class="main-header">🌍 Global Fleet Capacity Analysis (Hybrid View)</p>', unsafe_allow_html=True)

            for _, row in df_all.iterrows():
                lang_name = str(row.iloc[0]); target_workload_hrs = float(row.iloc[1])
                actual_hc_count = float(row.iloc[2]); shrink_val = float(row.iloc[3])
                shrink_p = shrink_val / 100 if shrink_val > 1 else shrink_val 
                actual_available_hrs = (actual_hc_count * base_hrs_per_person) * (1 - shrink_p)
                hrs_variance = actual_available_hrs - target_workload_hrs
                req_hc = np.ceil(target_workload_hrs / (base_hrs_per_person * (1 - shrink_p))) if base_hrs_per_person > 0 else 0
                hc_variance = actual_hc_count - req_hc

                with st.expander(f"🚩 Language: {lang_name.upper()}", expanded=True):
                    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
                    c1.metric("Tgt Hrs", f"{int(target_workload_hrs):,}h")
                    c2.metric("Act Hrs", f"{int(actual_available_hrs):,}h")
                    c3.metric("Hrs Var", f"{int(hrs_variance):,}h", delta=int(hrs_variance))
                    c4.metric("Shrink %", f"{shrink_p*100:.1f}%")
                    c5.metric("Req HC", f"{int(req_hc)}")
                    c6.metric("Act HC", f"{int(actual_hc_count)}")
                    c7.metric("HC Gap", f"{int(hc_variance)}", delta=int(hc_variance))
            st.divider()

    with tab2:
        # عرض البيانات تحت مسمى Resource Requirements
        if os.path.exists("intra_last.xlsx"):
            xls = pd.ExcelFile("intra_last.xlsx")
            avail_langs = [s for s in xls.sheet_names if "Sheet" not in s]
            op_lang = st.selectbox("🎯 Select Language", avail_langs, key="op_filter")
            st.session_state['active_lang'] = op_lang
            
            # العنوان المعدل داخل التابة
            st.subheader(f"🎯 Resource Requirements Analysis")
        
        xls = pd.ExcelFile("intra_last.xlsx")
            df_raw = pd.read_excel("intra_last.xlsx", sheet_name=op_lang, header=None)
            if not df_raw.empty:
                new_cols = ["Intervals"] + [pd.to_datetime(d).strftime('%Y-%m-%d') for d in df_raw.iloc[0, 1:]]
                df_intra = df_raw.drop(0).copy()
                df_intra.columns = new_cols
                df_intra['Intervals'] = df_intra['Intervals'].apply(format_time_index)
                st.session_state['df_intra'] = df_intra.set_index('Intervals').apply(pd.to_numeric, errors='coerce').fillna(0).round(0).astype(int)
                st.dataframe(st.session_state['df_intra'], use_container_width=True)

    with tab3:
        lang = st.session_state.get('active_lang')
        if os.path.exists("sched_last.xlsx") and lang:
            st.subheader(f"🗓️ Staff Coverage: {lang}")
            try:
                df_s = pd.read_excel("sched_last.xlsx", sheet_name=lang)
                intervals = pd.date_range("00:00", "23:30", freq="30min").strftime('%H:%M').tolist()
                df_s['Day'] = pd.to_datetime(df_s['Day'], errors='coerce')
                target_dates = pd.date_range(start_date, end_date).strftime('%Y-%m-%d').tolist()
                cov_dict = {"Intervals": intervals}
                for d_str in target_dates:
                    day_df = df_s[df_s['Day'].dt.strftime('%Y-%m-%d') == d_str]
                    counts = [0] * len(intervals)
                    for i, slot in enumerate(intervals):
                        slot_t = datetime.strptime(slot, '%H:%M').time()
                        for _, r in day_df.iterrows():
                            try:
                                st_v = str(r['Start Time']).strip().upper()
                                if st_v in ['OFF', 'NAN', '-', '']: continue
                                st_t, en_t = pd.to_datetime(st_v).time(), pd.to_datetime(str(r['End Time'])).time()
                                if (st_t <= slot_t < en_t) if st_t < en_t else (slot_t >= st_t or slot_t < en_t): counts[i] += 1
                            except: continue
                    cov_dict[d_str] = counts
                st.session_state['df_cov'] = pd.DataFrame(cov_dict).set_index('Intervals').astype(int)
                st.dataframe(st.session_state['df_cov'], use_container_width=True)
            except: st.error(f"Sheet '{lang}' not found.")

    with tab4:
        lang = st.session_state.get('active_lang')
        if 'df_intra' in st.session_state and 'df_cov' in st.session_state:
            st.subheader(f"⚖️ Efficiency Analysis: {lang}")
            d_intra = st.session_state['df_intra']
            d_cov = st.session_state['df_cov'].reindex(d_intra.index).fillna(0).astype(int)
            common_cols = [c for c in d_cov.columns if c in d_intra.columns]
            if common_cols:
                df_net = d_cov[common_cols] - d_intra[common_cols]
                st.dataframe(df_net.style.applymap(color_net_staffing), use_container_width=True)





