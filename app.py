import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime

st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# --- دالة التلوين (للعجز والزيادة بأرقام صحيحة) ---
def color_net_staffing(val):
    try:
        if val < 0: return 'background-color: #ffcccc; color: #900000; font-weight: bold'
        if val > 0: return 'background-color: #ccffcc; color: #006600'
    except: pass
    return ''

# --- دالة تنقية الشيتات (إلغاء أي شيت فيه كلمة Sheet) ---
def get_clean_sheets(xls_file):
    all_sheets = pd.ExcelFile(xls_file).sheet_names
    return [s for s in all_sheets if "Sheet" not in s]

tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity", "⏰ Intraday", "🗓️ Scheduling", "⚖️ Net Staffing"])

# --- التابة الأولى: الكابستي (إعدادات اللغة والرينج) ---
with tab1:
    with st.sidebar:
        st.header("⚙️ Global Settings")
        # فلتر الرينج اللي طلبته
        d_range = st.date_input("Select Date Range", [date(2026, 2, 1), date(2026, 2, 28)])
        start_date = d_range[0]
        end_date = d_range[1] if len(d_range) > 1 else d_range[0]
        
        main_file = st.file_uploader("Upload Data.xlsx (Capacity)", type=["xlsx"])
    
    if main_file:
        sel_lang = st.selectbox("Select Language (Main)", get_clean_sheets(main_file), key="main_lang")
        st.session_state['selected_lang'] = sel_lang # حفظ اللغة للتابات التانية
        
        df_cap = pd.read_excel(main_file, sheet_name=sel_lang)
        df_cap.columns = [str(c).strip().lower() for c in df_cap.columns]
        
        # معادلة الكابستي الأصلية
        working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
        base_hrs = working_days * 8
        
        col_t = next((c for c in df_cap.columns if 'target' in c), None)
        col_s = next((c for c in df_cap.columns if 'shrink' in c), None)
        
        if col_t and col_s:
            row = df_cap.iloc[0]
            shrink = float(row[col_s]) / 100 if float(row[col_s]) > 1 else float(row[col_s])
            req_hc = np.ceil(float(row[col_t]) / (base_hrs * (1 - shrink)))
            st.metric("Required HC (Integer)", int(req_hc))

# --- التابة الثانية: Intraday (تحويل إجباري لأرقام صحيحة) ---
with tab2:
    st.subheader("Half-Hour Interval Requirements")
    intra_file = st.file_uploader("Upload Required.xlsx", type=["xlsx"])
    if intra_file:
        lang = st.session_state.get('selected_lang', get_clean_sheets(intra_file)[0])
        df_raw = pd.read_excel(intra_file, sheet_name=lang, header=None)
        
        # معالجة الهيدر والوقت
        df_raw.columns = ["Intervals"] + [pd.to_datetime(v).strftime('%Y-%m-%d') if not isinstance(v, str) else v for v in df_raw.iloc[0, 1:]]
        df_intra = df_raw.drop(0).copy()
        df_intra['Intervals'] = pd.to_datetime(df_intra['Intervals'], errors='coerce').dt.strftime('%H:%M')
        df_intra = df_intra.dropna(subset=['Intervals'])
        
        # تحويل الأرقام لصحية (إلغاء الكسور)
        final_intra = df_intra.set_index('Intervals').apply(pd.to_numeric, errors='coerce').fillna(0).round(0).astype(int)
        st.session_state['df_intra'] = final_intra
        st.dataframe(final_intra, use_container_width=True)

# --- التابة الثالثة: Scheduling (توليد التغطية) ---
with tab3:
    st.subheader("Employee Staffing Schedules")
    sched_file = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"])
    if sched_file:
        lang = st.session_state.get('selected_lang', get_clean_sheets(sched_file)[0])
        df_s = pd.read_excel(sched_file, sheet_name=lang)
        
        intervals = pd.date_range("00:00", "23:30", freq="30min").strftime('%H:%M').tolist()
        df_s['Day'] = pd.to_datetime(df_s['Day'], errors='coerce')
        
        cov_dict = {"Intervals": intervals}
        for d_str in pd.date_range(start_date, end_date).strftime('%Y-%m-%d'):
            day_df = df_s[df_s['Day'].dt.strftime('%Y-%m-%d') == d_str]
            counts = []
            for slot in intervals:
                slot_t = datetime.strptime(slot, '%H:%M').time()
                c = 0
                for _, r in day_df.iterrows():
                    try:
                        if str(r['Start Time']).upper() in ['OFF', 'NAN', '-']: continue
                        if pd.to_datetime(str(r['Start Time'])).time() <= slot_t < pd.to_datetime(str(r['End Time'])).time(): c += 1
                    except: pass
                counts.append(c)
            cov_dict[d_str] = counts
            
        final_cov = pd.DataFrame(cov_dict).set_index('Intervals').astype(int)
        st.session_state['df_cov'] = final_cov
        st.dataframe(final_cov, use_container_width=True)

# --- التابة الرابعة: Net Staffing (طرح مباشر بدون None) ---
with tab4:
    if 'df_intra' in st.session_state and 'df_cov' in st.session_state:
        # التأكد من تطابق الأعمدة والصفوف لمنع الـ None
        d_intra = st.session_state['df_intra']
        d_cov = st.session_state['df_cov'].reindex(d_intra.index).fillna(0)
        
        common_cols = [c for c in d_cov.columns if c in d_intra.columns]
        if common_cols:
            df_net = d_cov[common_cols].astype(int) - d_intra[common_cols].astype(int)
            st.dataframe(df_net.style.applymap(color_net_staffing), use_container_width=True)
        else:
            st.warning("⚠️ No matching dates found between files.")
