import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime

st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# --- دالة التلوين (أرقام صحيحة) ---
def color_net_staffing(val):
    if isinstance(val, (int, float)):
        if val < 0: return 'background-color: #ffcccc; color: #900000; font-weight: bold'
        if val > 0: return 'background-color: #ccffcc; color: #006600'
    return ''

# --- دالة تنقية الشيتات ---
def get_clean_sheets(xls_file):
    all_sheets = pd.ExcelFile(xls_file).sheet_names
    return [s for s in all_sheets if "Sheet" not in s]

tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity", "⏰ Intraday", "🗓️ Scheduling", "⚖️ Net Staffing"])

# ---------------------------------------------------------
# TAB 1: CAPACITY PLANNING (العودة للأصل مع الفلتر)
# ---------------------------------------------------------
with tab1:
    st.subheader("Monthly Capacity Analysis")
    with st.sidebar:
        st.header("⚙️ Global Settings")
        start_date = st.date_input("Start Date", date(2026, 2, 1))
        end_date = st.date_input("End Date", date(2026, 2, 28))
        # فلتر التاريخ لمشاهدة يوم محدد في كل التابات
        selected_day = st.date_input("Filter by Specific Day", date(2026, 2, 2))
        
        # حساب أيام العمل والساعات
        working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
        base_hours = working_days * 8
        st.info(f"📅 Working Days: {working_days} | ⏳ Base Hours: {base_hours}")
        
        main_file = st.file_uploader("Upload Data.xlsx", type=["xlsx"], key="cap_up")

    if main_file:
        clean_sheets = get_clean_sheets(main_file)
        sel_lang = st.selectbox("Select Language (Capacity)", clean_sheets)
        df_cap = pd.read_excel(main_file, sheet_name=sel_lang)
        df_cap.columns = [str(c).strip().lower() for c in df_cap.columns]
        
        col_t = next((c for c in df_cap.columns if 'target' in c), None)
        col_a = next((c for c in df_cap.columns if 'actual' in c), None)
        col_s = next((c for c in df_cap.columns if 'shrink' in c), None)

        if all([col_t, col_a, col_s]):
            row = df_cap.iloc[0]
            shrink_p = float(row[col_s]) if float(row[col_s]) < 1 else float(row[col_s]) / 100
            n_cap = base_hours * (1 - shrink_p)
            req_hc = np.ceil(float(row[col_t]) / n_cap) if n_cap > 0 else 0
            
            # عرض الكابستي زي الأول
            c1, c2, c3 = st.columns(3)
            c1.metric("Target Hours", f"{int(row[col_t])}h")
            c2.metric("Required HC", int(req_hc))
            c3.metric("HC Variance", int(float(row[col_a]) - req_hc), delta=int(float(row[col_a]) - req_hc))

# ---------------------------------------------------------
# TAB 2: INTRADAY (أرقام صحيحة + فلتر تاريخ)
# ---------------------------------------------------------
with tab2:
    st.subheader("Half-Hour Interval Requirements")
    intra_file = st.file_uploader("Upload Required.xlsx", type=["xlsx"], key="int_up")
    if intra_file:
        lang_int = st.selectbox("Select Language (Intraday)", get_clean_sheets(intra_file))
        df_raw = pd.read_excel(intra_file, sheet_name=lang_int, header=None)
        
        h_row = df_raw.iloc[0].values
        new_cols = ["Intervals"]
        for v in h_row[1:]:
            try: new_cols.append(pd.to_datetime(v).strftime('%Y-%m-%d'))
            except: new_cols.append(str(v))
        
        df_intra = df_raw.drop(0).copy()
        df_intra.columns = new_cols
        df_intra['Intervals'] = pd.to_datetime(df_intra['Intervals'], errors='coerce').dt.strftime('%H:%M')
        df_intra = df_intra.dropna(subset=['Intervals'])
        
        # تحويل لأرقام صحيحة
        final_intra = df_intra.set_index('Intervals').apply(pd.to_numeric, errors='coerce').fillna(0).round(0).astype(int)
        st.session_state['df_intra'] = final_intra
        
        # تطبيق فلتر التاريخ
        day_str = selected_day.strftime('%Y-%m-%d')
        if day_str in final_intra.columns:
            st.write(f"📅 Showing Data for: {day_str}")
            st.dataframe(final_intra[[day_str]], use_container_width=True)
        else:
            st.dataframe(final_intra, use_container_width=True)

# ---------------------------------------------------------
# TAB 3: SCHEDULING (أرقام صحيحة + فلتر تاريخ)
# ---------------------------------------------------------
with tab3:
    st.subheader("Employee Staffing Coverage")
    sched_file = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"], key="sch_up")
    if sched_file:
        lang_sch = st.selectbox("Select Language (Schedule)", get_clean_sheets(sched_file))
        df_s = pd.read_excel(sched_file, sheet_name=lang_sch)
        
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
                        st_v = str(r['Start Time']).strip().upper()
                        if st_v in ['OFF', 'NAN', '-']: continue # معالجة الشرطات
                        st_t = pd.to_datetime(st_v).time()
                        en_t = pd.to_datetime(str(r['End Time'])).time()
                        if st_t <= slot_t < en_t: c += 1
                    except: continue
                counts.append(c)
            cov_dict[d_str] = counts
            
        final_cov = pd.DataFrame(cov_dict).set_index('Intervals').astype(int)
        st.session_state['df_cov'] = final_cov
        
        day_str = selected_day.strftime('%Y-%m-%d')
        if day_str in final_cov.columns:
            st.dataframe(final_cov[[day_str]], use_container_width=True)
        else:
            st.dataframe(final_cov, use_container_width=True)

# ---------------------------------------------------------
# TAB 4: NET STAFFING (المقارنة بالأرقام الصحيحة)
# ---------------------------------------------------------
with tab4:
    if 'df_intra' in st.session_state and 'df_cov' in st.session_state:
        d_intra = st.session_state['df_intra']
        d_cov = st.session_state['df_cov']
        common_cols = [c for c in d_cov.columns if c in d_intra.columns]
        
        if common_cols:
            d_cov_aligned = d_cov.reindex(d_intra.index).fillna(0).astype(int)
            df_net = d_cov_aligned[common_cols] - d_intra[common_cols]
            
            day_str = selected_day.strftime('%Y-%m-%d')
            if day_str in df_net.columns:
                st.write(f"⚖️ Gap Analysis for: {day_str}")
                st.dataframe(df_net[[day_str]].style.applymap(color_net_staffing), use_container_width=True)
            else:
                st.dataframe(df_net.style.applymap(color_net_staffing), use_container_width=True)
