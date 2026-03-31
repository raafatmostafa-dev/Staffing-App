import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time
import os
import base64

# --- 1. إعدادات الصفحة والتصميم الفاخر ---
st.set_page_config(page_title="WFM Professional Suite", layout="wide", initial_sidebar_state="collapsed")

# تصميم CSS متقدم "Chic & Minimalist"
st.markdown("""
    <style>
    /* تحسين الخطوط والخلفية */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        background-color: #010411;
    }

    /* إخفاء العناصر غير الضرورية */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"] { display: none; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* تصميم الـ Tabs لتبدو كأزرار احترافية */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #010411;
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
        color: #64748B;
        border: 1px solid #E2E8F0;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A !important;
        color: white !important;
        border: 1px solid #1E3A8A !important;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.2);
    }

    /* كروت البيانات (Cards) */
    .metric-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #F1F5F9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
    }

    /* تحسين شكل الـ Metric الافتراضي لستريمليت */
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #F1F5F9;
        padding: 15px;
        border-radius: 10px;
    }
    
    /* العناوين */
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -1px;
        margin-bottom: 30px;
    }
    
    /* تنسيق الجداول */
    .styled-table {
        border-radius: 10px;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

def save_file(uploaded_file, name):
    with open(name, "wb") as f:
        f.write(uploaded_file.getbuffer())

# --- 2. نظام تسجيل الدخول (تصميم العميق المطور) ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("""
        <style>
        /* إضافة الخلفية العميقة باستخدام الصورة التي رفعتها */
        .stApp {
            background: linear-gradient(rgba(1, 4, 17, 0.7), rgba(1, 4, 17, 0.8)), 
                        url('https://www.storyblocks.com/video/stock/digital-cyberspace-with-particles-and-digital-data-network-connections-high-speed-connection-and-data-analysis-technology-abstract-background-concept-bkp--fkwj4sh9u25');
            background-size: cover;
            background-position: center;
        }

        /* شعار Kalam في الأعلى على الشمال */
        .kalam-logo {
            position: absolute;
            top: 20px;
            left: 30px;
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: 1.8rem;
            color: #00F6FF; /* أزرق متوهج */
            text-shadow: 0 0 10px rgba(0, 246, 255, 0.5);
            z-index: 999;
        }

        .login-card {
            background: rgba(255, 255, 255, 0.05); /* شفافية عالية للعمق */
            backdrop-filter: blur(25px) saturate(150%); /* تغبيش قوي */
            padding: 50px 40px;
            border-radius: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 40px 100px rgba(0,0,0,0.5);
            text-align: center;
            margin-bottom: -40px;
        }
        
        .brand-name {
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: 2.6rem;
            color: white;
            letter-spacing: -2px;
            margin-bottom: 5px;
            text-shadow: 0 0 20px rgba(255,255,255,0.2);
        }
        
        .brand-sub {
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.9rem;
            margin-bottom: 30px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        /* تحسين شكل حقول الإدخال لتناسب العمق */
        .stTextInput input {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border-radius: 12px !important;
        }
        </style>
        
        <div class="kalam-logo">Kalam</div>
        
        <div style='height: 100px;'></div>
    """, unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("""
            <div class="login-card">
                <div class="brand-name">WFM Data</div>
                <div class="brand-sub">Next-Gen Analytics Portal</div>
            </div>
        """, unsafe_allow_html=True)
        
        user = st.text_input("Username", placeholder="Identity")
        pw = st.text_input("Password", type="password", placeholder="••••••••")
        
        if st.button("Authenticate System", use_container_width=True):
            if user == "Raafat Mostafa" and pw == "Rr#01010353831":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("🔒 Security Mismatch")
    st.stop()

# --- 3. التطبيق الرئيسي ---
st.markdown('<h1 class="main-header">Workforce Management Dashboard</h1>', unsafe_allow_html=True)

def color_net_staffing(val):
    try:
        if val < 0: return 'background-color: #FFF1F2; color: #BE123C; font-weight: bold; border: 1px solid #FECDD3'
        if val > 0: return 'background-color: #F0FDF4; color: #15803D; border: 1px solid #DCFCE7'
    except: pass
    return ''

def format_time_index(t):
    if isinstance(t, (time, datetime)): return t.strftime('%H:%M')
    try: return pd.to_datetime(str(t)).strftime('%H:%M')
    except: return str(t)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Executive Summary", "🎯 Requirements", "🗓️ Schedule View", "⚖️ Delta Analysis"])

with tab1:
    with st.expander("🛠️ Control Panel & Data Ingestion", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            d_range = st.date_input("Analysis Window", [date(2026, 4, 1), date(2026, 4, 30)])
        with c2:
            up_main = st.file_uploader("Upload Core Data", type=["xlsx"])
            if up_main: save_file(up_main, "data_last.xlsx")
        with c3:
            up_intra = st.file_uploader("Upload Intrady Requirements", type=["xlsx"])
            if up_intra: save_file(up_intra, "intra_last.xlsx")
            up_sched = st.file_uploader("Upload Master Schedules", type=["xlsx"])
            if up_sched: save_file(up_sched, "sched_last.xlsx")

    start_date = d_range[0]
    end_date = d_range[1] if len(d_range) > 1 else d_range[0]

    if os.path.exists("data_last.xlsx"):
        df_all = pd.read_excel("data_last.xlsx", sheet_name=0)
        working_days = np.busday_count(np.datetime64(start_date), np.datetime64(end_date) + np.timedelta64(1, 'D'))
        base_hrs_per_person = working_days * 8
        
        # 1. تجميع البيانات وحساب القيم
        chart_records = []
        for _, row in df_all.iterrows():
            l_name = str(row.iloc[0])
            t_load = float(row.iloc[1])
            a_hc = float(row.iloc[2])
            s_val = float(row.iloc[3])
            s_p = s_val / 100 if s_val > 1 else s_val 
            s_cap = (a_hc * base_hrs_per_person) * (1 - s_p)
            
            chart_records.append({
                "Language": l_name,
                "Target Load": t_load,
                "Supply Cap": s_cap
            })

        # 2. الترتيب الفعلي (Sorting)
        df_plot = pd.DataFrame(chart_records).sort_values(by="Target Load", ascending=False)
        
        st.markdown("### 📊 Sorted Load vs Supply Analysis")

        # 3. استخدام Plotly لضمان ثبات الترتيب (أكثر احترافية)
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_plot["Language"], y=df_plot["Target Load"], name='Target Load', marker_color='#1E3A8A'))
        fig.add_trace(go.Bar(x=df_plot["Language"], y=df_plot["Supply Cap"], name='Supply Cap', marker_color='#00F6FF'))

        fig.update_layout(
            barmode='group',
            xaxis={'categoryorder':'total descending'}, # هذا السطر يضمن الترتيب التنازلي
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0),
            height=250,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("<hr style='border: 0.5px solid #E2E8F0; margin: 40px 0;'>", unsafe_allow_html=True)

        # 4. عرض الكروت بناءً على نفس الترتيب
        for _, row_data in df_plot.iterrows():
            lang_name = row_data["Language"]
            target_workload_hrs = row_data["Target Load"]
            actual_available_hrs = row_data["Supply Cap"]
            
            # جلب باقي البيانات من الجدول الأصلي للكروت
            orig = df_all[df_all.iloc[:, 0] == lang_name].iloc[0]
            act_hc = float(orig.iloc[2])
            shrink_val = float(orig.iloc[3])
            shrink_p = shrink_val / 100 if shrink_val > 1 else shrink_val 

            hrs_variance = actual_available_hrs - target_workload_hrs
            req_hc = np.ceil(target_workload_hrs / (base_hrs_per_person * (1 - shrink_p))) if base_hrs_per_person > 0 else 0
            hc_var = act_hc - req_hc

            with st.container():
                st.markdown(f"<div style='background: #1E3A8A; padding: 10px 20px; border-radius: 10px 10px 0 0; color: white;'><span style='font-weight: 800;'>🌍 {lang_name.upper()}</span></div>", unsafe_allow_html=True)
                m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
                m1.metric("Target Load", f"{int(target_workload_hrs):,}h")
                m2.metric("Supply Cap", f"{int(actual_available_hrs):,}h")
                m3.metric("Hrs Delta", f"{int(hrs_variance):,}h", delta=int(hrs_variance))
                m4.metric("Shrinkage", f"{shrink_p*100:.1f}%")
                m5.metric("Required HC", int(req_hc))
                m6.metric("Active HC", int(act_hc))
                m7.metric("HC Gap", int(hc_var), delta=int(hc_var))
                st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
with tab2:
    if os.path.exists("intra_last.xlsx"):
        xls = pd.ExcelFile("intra_last.xlsx")
        avail_langs = [s for s in xls.sheet_names if "Sheet" not in s]
        st.markdown("### 🎯 Resource Profiling")
        op_lang = st.selectbox("Active Viewport:", avail_langs, key="op_filter")
        st.session_state['active_lang'] = op_lang
        
        df_raw = pd.read_excel("intra_last.xlsx", sheet_name=op_lang, header=None)
        if not df_raw.empty:
            new_cols = ["Intervals"] + [pd.to_datetime(d).strftime('%Y-%m-%d') for d in df_raw.iloc[0, 1:]]
            df_intra = df_raw.drop(0).copy()
            df_intra.columns = new_cols
            df_intra['Intervals'] = df_intra['Intervals'].apply(format_time_index)
            final_df_intra = df_intra.set_index('Intervals').apply(pd.to_numeric, errors='coerce').fillna(0).round(0).astype(int)
            st.session_state['df_intra'] = final_df_intra
            st.dataframe(final_df_intra.style.background_gradient(cmap="Blues", axis=None), use_container_width=True)

with tab3:
    lang = st.session_state.get('active_lang')
    if os.path.exists("sched_last.xlsx") and lang:
        st.markdown(f"### 🗓️ Coverage Heatmap: <span style='color:#1E3A8A'>{lang}</span>", unsafe_allow_html=True)
        try:
            df_s = pd.read_excel("sched_last.xlsx", sheet_name=lang)
            df_s['Day'] = pd.to_datetime(df_s['Day']).dt.date
            intervals = pd.date_range("00:00", "23:30", freq="30min").strftime('%H:%M').tolist()
            target_dates = pd.date_range(start_date, end_date).date.tolist()
            df_coverage = pd.DataFrame(0, index=intervals, columns=[d.strftime('%Y-%m-%d') for d in target_dates])

            for _, r in df_s.iterrows():
                if pd.isna(r['Day']): continue
                curr_day = r['Day']
                try:
                    st_v, en_v = str(r['Start Time']).strip().upper(), str(r['End Time']).strip().upper()
                    if st_v in ['OFF', 'NAN', '-', ''] or en_v in ['OFF', 'NAN', '-', '']: continue
                    start_t = pd.to_datetime(st_v).time()
                    end_t = pd.to_datetime(en_v).time()
                    
                    for slot in intervals:
                        slot_t = datetime.strptime(slot, '%H:%M').time()
                        if start_t < end_t:
                            if start_t <= slot_t < end_t:
                                day_str = curr_day.strftime('%Y-%m-%d')
                                if day_str in df_coverage.columns: df_coverage.at[slot, day_str] += 1
                        else: # Night Shift
                            if slot_t >= start_t:
                                day_str = curr_day.strftime('%Y-%m-%d')
                                if day_str in df_coverage.columns: df_coverage.at[slot, day_str] += 1
                            elif slot_t < end_t:
                                next_day = curr_day + pd.Timedelta(days=1)
                                next_day_str = next_day.strftime('%Y-%m-%d')
                                if next_day_str in df_coverage.columns: df_coverage.at[slot, next_day_str] += 1
                except: continue

            st.session_state['df_cov'] = df_coverage
            st.dataframe(df_coverage.style.background_gradient(cmap="Greens", axis=None), use_container_width=True)
        except Exception as e:
            st.error(f"⚠️ Technical Alert: {e}")

with tab4:
    lang = st.session_state.get('active_lang')
    if 'df_intra' in st.session_state and 'df_cov' in st.session_state:
        st.markdown(f"### ⚖️ Net Staffing Variance: <span style='color:#1E3A8A'>{lang}</span>", unsafe_allow_html=True)
        d_intra = st.session_state['df_intra']
        d_cov = st.session_state['df_cov'].reindex(d_intra.index).fillna(0).astype(int)
        common_cols = [c for c in d_cov.columns if c in d_intra.columns]
        if common_cols:
            df_net = d_cov[common_cols] - d_intra[common_cols]
            st.dataframe(df_net.style.map(color_net_staffing), use_container_width=True)
    else:
        st.info("💡 Awaiting data ingestion. Please upload files and select a scope to view delta analysis.")
