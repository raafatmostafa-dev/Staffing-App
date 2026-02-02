import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

st.set_page_config(page_title="Workforce Gap Analysis", layout="wide")

st.title("📊 Workforce Gap Analysis Calculator")
st.write("حساب الفرق بين الهيد كاونت المطلوب والحالي بناءً على معادلة الساعات والشرينكيدج")

# --- 1. إعدادات المدخلات (الـ Sidebar) ---
st.sidebar.header("⚙️ إعدادات الحساب (F3, F4, L4)")

# اختيار التواريخ لحساب NETWORKDAYS (F3, F4)
start_date = st.sidebar.date_input("Start Date (F3)", date(2024, 1, 1))
end_date = st.sidebar.date_input("End Date (F4)", date(2024, 1, 31))

# تحويل التواريخ لصيغة يفهمها بايثون لحساب أيام العمل
start_np = np.datetime64(start_date, 'D')
end_np = np.datetime64(end_date, 'D') + np.timedelta64(1, 'D')
working_days = np.busday_count(start_np, end_np)

# نسبة الشرينكيدج (L4)
shrinkage_pct = st.sidebar.slider("Shrinkage % (L4)", 0, 100, 20) / 100

# المعادلة: NETWORKDAYS * 8
total_monthly_hours_per_agent = working_days * 8

# سعة الموظف الصافية بعد الشرينكيدج: (Hours * (1 - Shrinkage))
net_capacity_per_agent = total_monthly_hours_per_agent * (1 - shrinkage_pct)

st.sidebar.divider()
st.sidebar.write(f"📅 Working Days: **{working_days}**")
st.sidebar.write(f"⏳ Net Capacity/Agent: **{round(net_capacity_per_agent, 2)}** hrs")

# --- 2. رفع الملف ومعالجته ---
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # قراءة الملف (سواء إكسيل أو CSV)
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, encoding='cp1256')
        
        # تنظيف أسامي الأعمدة
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # البحث عن أعمدة اللغة والساعات
        col_lang = next((c for c in df.columns if 'lang' in c or 'لغة' in c), None)
        col_hours = next((c for c in df.columns if 'hour' in c or 'ساع' in c), None)

        if col_lang and col_hours:
            # تجميع الساعات المطلوبة لكل لغة
            summary = df.groupby(col_lang)[col_hours].sum().reset_index()
            summary.columns = ['Language', 'Target Hours']

            # حساب الهيد كاونت المطلوب (Target Hours / Net Capacity)
            summary['Required HC'] = (summary['Target Hours'] / net_capacity_per_agent).replace([np.inf, -np.inf], 0).apply(np.ceil)

            st.subheader("📝 Analysis Result per Language")
            
            final_results = []
            for _, row in summary.iterrows():
                lang = row['Language']
                target_hrs = row['Target Hours']
                req_hc = row['Required HC']
                
                with st.expander(f"Analysis for: {lang}"):
                    c1, c2, c3 = st.columns(3)
                    
                    # إدخال الهيد كاونت الفعلي
                    actual_hc = c1.number_input(f"Actual HC ({lang})", value=0, key=f"hc_{lang}")
                    
                    # حساب الفارق في الهيد كاونت (معادلتك: Actual HC - Required HC)
                    # مع العلم إن الـ Required HC محسوب فيه الشرينكيدج أصلاً
                    hc_variance = actual_hc - req_hc
                    
                    # حساب الساعات المتاحة فعلياً بناءً على العدد الحالي
                    actual_available_hours = actual_hc * net_capacity_per_agent
                    
                    c2.metric("Target Hours", f"{round(target_hrs)} hr")
                    c3.metric("Available Hours", f"{round(actual_available_hours)} hr")
                    
                    if hc_variance < 0:
                        st.error(f"⚠️ Shortage: You are short of {abs(int(hc_variance))} agents.")
                    elif hc_variance > 0:
                        st.success(f"✅ Surplus: You have {int(hc_variance)} extra agents.")
                    else:
                        st.info("👌 Properly Staffed.")
                    
                    final_results.append({
                        "Language": lang,
                        "Target Hours": target_hrs,
                        "Required HC": req_hc,
                        "Actual HC": actual_hc,
                        "Variance (HC)": hc_variance
                    })

            st.divider()
            st.subheader("📊 Summary Table")
            st.table(pd.DataFrame(final_results))

        else:
            st.error("❌ الملف لازم يحتوي على عمود للغة (Language) وعمود للساعات (Hours)")
            
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
