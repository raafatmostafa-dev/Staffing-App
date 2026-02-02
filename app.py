import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

st.set_page_config(page_title="Workforce Planner", layout="wide")

st.title("📊 Language-Based Workforce Analysis")

# --- 1. إعدادات الوقت (NETWORKDAYS) ---
st.sidebar.header("🗓️ Monthly Period")
start_date = st.sidebar.date_input("Start Date (F3)", date(2024, 1, 1))
end_date = st.sidebar.date_input("End Date (F4)", date(2024, 1, 31))

# حساب أيام العمل الفعلية
start_np = np.datetime64(start_date, 'D')
end_np = np.datetime64(end_date, 'D') + np.timedelta64(1, 'D')
working_days = np.busday_count(start_np, end_np)
total_hours_month = working_days * 8

st.sidebar.info(f"Working Days: {working_days}")
st.sidebar.info(f"Total Hours/Month: {total_hours_month}")

uploaded_file = st.file_uploader("Upload Your Excel Sheet", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # قراءة الملف
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, encoding='cp1256')
        
        # تنظيف أسماء الأعمدة
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # البحث عن الأعمدة الأساسية
        col_lang = next((c for c in df.columns if 'lang' in c or 'لغة' in c), None)
        col_target = next((c for c in df.columns if 'target' in c or 'hour' in c or 'مطلوب' in c), None)
        col_actual = next((c for c in df.columns if 'actual' in c or 'hc' in c or 'فعلي' in c), None)
        col_shr = next((c for c in df.columns if 'shrink' in c or 'شرينك' in c), None)

        if col_lang and col_target:
            # تجميع البيانات لكل لغة
            agg_dict = {col_target: 'sum'}
            if col_actual: agg_dict[col_actual] = 'max'
            if col_shr: agg_dict[col_shr] = 'max'
            
            summary = df.groupby(col_lang).agg(agg_dict).reset_index()
            
            st.subheader("📝 Analysis per Language")
            final_report = []

            for _, row in summary.iterrows():
                lang_name = str(row[col_lang])
                with st.expander(f"Analysis for: {lang_name}", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    
                    # سحب القيم من الشيت أو وضع قيم افتراضية
                    initial_hc = float(row[col_actual]) if col_actual else 0.0
                    initial_shr = float(row[col_shr]) if col_shr else 20.0
                    
                    # مدخلات لكل لغة
                    actual_hc = c1.number_input(f"Actual HC ({lang_name})", value=initial_hc, key=f"hc_{lang_name}")
                    shrink_val = c2.number_input(f"Shrinkage % ({lang_name})", value=initial_shr, key=f"sh_{lang_name}") / 100
                    
                    # --- المعادلات المطلوبة ---
                    # 1. سعة الموظف = (أيام العمل * 8) * (1 - شرينكيدج اللغة)
                    lang_cap = total_hours_month * (1 - shrink_val)
                    
                    # 2. المطلوب = التارجت هاورز / سعة الموظف
                    target_hrs = row[col_target]
                    req_hc = np.ceil(target_hrs / lang_cap) if lang_cap > 0 else 0
                    
                    # 3. الفارق (بناءً على كلامك: الفعلي - المطلوب)
                    variance_hc = actual_hc - req_hc
                    
                    # 4. الساعات الفعلية المتاحة بناءً على الهيد كاونت اللي إنت حاطه
                    avail_hrs = actual_hc * lang_cap
                    
                    c3.metric("Required HC", int(req_hc))
                    
                    st.write(f"**Target:** {round(target_hrs,1)} hrs | **Available:** {round(avail_hrs,1)} hrs")
                    
                    if variance_hc < 0:
                        st.error(f"🔴 Shortage of {abs(int(variance_hc))} agents")
                    else:
                        st.success(f"🟢 Surplus of {int(variance_hc)} agents")
                        
                    final_report.append({
                        "Language": lang_name,
                        "Target Hours": round(target_hrs, 1),
                        "Actual HC": int(actual_hc),
                        "Required HC": int(req_hc),
                        "Variance (HC)": int(variance_hc)
                    })

            st.divider()
            st.subheader("📊 Final Summary Table")
            st.table(pd.DataFrame(final_report))
            
        else:
            st.error("❌ الملف ناقص! لازم يكون فيه أعمدة (Language) و (Hours/Target)")

    except Exception as e:
        st.error(f"Error in Processing: {e}")
