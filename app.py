import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

# إعدادات الصفحة الاحترافية
st.set_page_config(page_title="WFM Professional Planner", layout="wide")

# --- CSS لتغيير الواجهة بالكامل ---
st.markdown("""
    <style>
    /* تغيير خلفية الصفحة */
    .stApp {
        background-color: #F0F2f6;
    }
    /* تنسيق الكروت (Metrics) */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #1E3A8A;
    }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #E5E7EB;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    /* تنسيق العناوين */
    h1 { color: #1E3A8A; font-family: 'Segoe UI', sans-serif; }
    h3 { color: #3B82F6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Workforce Gap Analysis")
st.markdown("---")

# --- Sidebar الإعدادات ---
with st.sidebar:
    st.header("⚙️ Global Settings")
    # تواريخ NETWORKDAYS (F3, F4)
    start_date = st.date_input("Start Date (F3)", date(2026, 2, 1))
    end_date = st.date_input("End Date (F4)", date(2026, 2, 28))
    
    # حساب أيام العمل
    start_np = np.datetime64(start_date, 'D')
    end_np = np.datetime64(end_date, 'D') + np.timedelta64(1, 'D')
    working_days = np.busday_count(start_np, end_np)
    base_hours = working_days * 8
    
    st.info(f"📅 Working Days: {working_days}")
    st.info(f"⏳ Total Hours: {base_hours}")
    
    uploaded_file = st.file_uploader("Upload Data.xlsx", type=["xlsx"])

# --- معالجة وعرض البيانات ---
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # ربط الأعمدة بملفك بالظبط
        col_lang = "languages"
        col_target = "monthly target hours hours"
        col_actual = "actual hc"
        col_shr = "shrinkage"

        st.subheader("🔍 Language Analysis")
        
        # عرض البيانات في صفوف منظمة
        for _, row in df.iterrows():
            lang = row[col_lang]
            target_hrs = row[col_target]
            # قراءة قيم الملف كقيم افتراضية
            init_hc = float(row[col_actual])
            init_shr = float(row[col_shr]) * 100 if float(row[col_shr]) < 1 else float(row[col_shr])

            with st.container():
                st.markdown(f"### 🌐 {lang}")
                c1, c2, c3, c4 = st.columns(4)
                
                # مدخلات تفاعلية
                act_hc = c1.number_input(f"Actual HC", value=init_hc, key=f"hc_{lang}")
                shr_val = c2.number_input(f"Shrinkage %", value=init_shr, key=f"sh_{lang}") / 100
                
                # الحسابات (معادلتك)
                net_cap = base_hours * (1 - shr_val)
                req_hc = np.ceil(target_hrs / net_cap) if net_cap > 0 else 0
                
                # حساب الفارق بالساعات
                avail_hrs = act_hc * net_cap
                hr_variance = avail_hrs - target_hrs
                
                # العرض الاحترافي
                c3.metric("Required HC", int(req_hc), delta=int(act_hc - req_hc))
                
                # لون الفارق بالساعات
                c4.metric("Hour Variance", f"{round(hr_variance)} hr", 
                          delta=round(hr_variance), 
                          delta_color="normal")
                
                st.markdown("---")

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
else:
    st.warning("👈 برجاء رفع ملف الإكسيل من القائمة الجانبية للبدء.")
