import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

# إعدادات الصفحة
st.set_page_config(page_title="WFM Comprehensive Dashboard", layout="wide")

# --- تحسين الواجهة CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #E5E7EB;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    h4 { color: #1E3A8A; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Workforce Comprehensive Analysis")
st.markdown("---")

# --- Sidebar الإعدادات ---
with st.sidebar:
    st.header("📅 Period Settings")
    start_date = st.date_input("Start Date (F3)", date(2026, 2, 1))
    end_date = st.date_input("End Date (F4)", date(2026, 2, 28))
    
    # حساب أيام العمل (NETWORKDAYS)
    start_np = np.datetime64(start_date, 'D')
    end_np = np.datetime64(end_date, 'D') + np.timedelta64(1, 'D')
    working_days = np.busday_count(start_np, end_np)
    base_hours = working_days * 8
    
    st.info(f"Working Days: {working_days}")
    st.info(f"Base Hours: {base_hours}")
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload Data.xlsx", type=["xlsx"])

# --- معالجة وعرض البيانات ---
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        # تنظيف أسامي الأعمدة لتطابق ملفك
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # ربط الأعمدة حسب ملفك
        col_lang = "languages"
        col_target_hrs = "monthly target hours hours"
        col_actual_hc = "actual hc"
        col_shr = "shrinkage"

        if col_lang in df.columns and col_target_hrs in df.columns:
            st.subheader("📋 Language Metrics (Target vs Actual)")

            for _, row in df.iterrows():
                lang = row[col_lang]
                target_hrs = float(row[col_target_hrs])
                
                # سحب القيم من الملف
                init_hc = float(row[col_actual_hc])
                # تحويل الكسر لنسبة مئوية لو كان أقل من 1
                raw_shr = float(row[col_shr])
                init_shr = raw_shr * 100 if raw_shr < 1 else raw_shr

                with st.container():
                    st.markdown(f"#### 🌐 {lang}")
                    
                    # مدخلات التعديل
                    in_col1, in_col2 = st.columns(2)
                    u_hc = in_col1.number_input(f"Actual HC ({lang})", value=init_hc, key=f"hc_{lang}")
                    u_shr_pct = in_col2.number_input(f"Shrinkage % ({lang})", value=init_shr, key=f"sh_{lang}") / 100
                    
                    # الحسابات بناءً على معادلاتك
                    net_capacity = base_hours * (1 - u_shr_pct)
                    t_hc = np.ceil(target_hrs / net_capacity) if net_capacity > 0 else 0
                    
                    # الساعات الفعلية المتاحة (Actual HC * Net Capacity)
                    a_hrs = u_hc * net_capacity
                    
                    # الفوارق (Variances)
                    hr_variance = a_hrs - target_hrs
                    hc_variance = u_hc - t_hc

                    # عرض الـ 6 أرقام المطلوبة
                    m1, m2, m3, m4, m5, m6 = st.columns(6)
                    
                    m1.metric("Target Hours", f"{round(target_hrs)}h")
                    m2.metric("Actual Hours", f"{round(a_hrs)}h")
                    m3.metric("Hrs Variance", f"{round(hr_variance)}h", delta=round(hr_variance))
                    
                    m4.metric("Target HC", int(t_hc))
                    m5.metric("Actual HC", int(u_hc))
                    m6.metric("HC Variance", int(hc_variance), delta=int(hc_variance))
                    
                    st.divider()
        else:
            st.error("❌ الأعمدة المطلوبة غير موجودة في الملف. تأكد من وجود 'languages' و 'monthly target hours hours'.")

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
else:
    st.info("👈 ارفع ملف 'Data.xlsx' عشان الحسابات تظهر.")
