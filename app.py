import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

st.set_page_config(page_title="Workforce Gap Analysis", layout="wide")

st.title("📊 Workforce Gap Analysis Calculator")

# --- 1. إعدادات الحساب ---
st.sidebar.header("⚙️ إعدادات الحساب")
start_date = st.sidebar.date_input("Start Date", date(2024, 1, 1))
end_date = st.sidebar.date_input("End Date", date(2024, 1, 31))

# حساب أيام العمل الشهرية
start_np = np.datetime64(start_date, 'D')
end_np = np.datetime64(end_date, 'D') + np.timedelta64(1, 'D')
working_days = np.busday_count(start_np, end_np)

# نسبة الشرينكيدج
shrinkage_pct = st.sidebar.slider("Shrinkage %", 0, 100, 20) / 100

# سعة الموظف الشهرية الصافية (معادلتك بالظبط)
monthly_net_cap = (working_days * 8) * (1 - shrinkage_pct)

# سعة الموظف الأسبوعية (عشان لو الداتا بالأسابيع)
weekly_net_cap = monthly_net_cap / 4

st.sidebar.info(f"سعة الموظف في الشهر: {round(monthly_net_cap, 1)} ساعة")
st.sidebar.info(f"سعة الموظف في الأسبوع: {round(weekly_net_cap, 1)} ساعة")

uploaded_file = st.file_uploader("Upload File", type=["xlsx", "csv"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, encoding='cp1256')
        
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        col_lang = next((c for c in df.columns if 'lang' in c or 'لغة' in c), None)
        col_hours = next((c for c in df.columns if 'hour' in c or 'ساع' in c), None)

        if col_lang and col_hours:
            # التعديل الجوهري: بناخد "المتوسط الأسبوعي" للساعات مش المجموع الكلي
            summary = df.groupby(col_lang)[col_hours].mean().reset_index()
            summary.columns = ['Language', 'Avg Weekly Hours']

            # المطلوب = متوسط ساعات الأسبوع / سعة الموظف الأسبوعية
            summary['Required HC'] = (summary['Avg Weekly Hours'] / weekly_net_cap).apply(np.ceil)

            st.subheader("📝 التحليل بناءً على متوسط الساعات الأسبوعية")
            
            final_results = []
            for _, row in summary.iterrows():
                with st.expander(f"اللغة: {row['Language']}"):
                    c1, c2 = st.columns(2)
                    actual_hc = c1.number_input(f"Actual HC ({row['Language']})", value=0, key=f"hc_{row['Language']}")
                    
                    # الحسبة اللي إنت طلبتها: (الفعلي * السعة) - (المطلوب * السعة)
                    actual_hours = actual_hc * weekly_net_cap
                    target_hours = row['Avg Weekly Hours']
                    variance_hours = actual_hours - target_hours
                    
                    c2.metric("Target Hours (Wk)", f"{round(target_hours)} hr")
                    st.metric("Variance (Hours)", f"{round(variance_hours, 1)} hr", delta=round(variance_hours, 1))
                    
                    final_results.append({
                        "Language": row['Language'],
                        "Avg Weekly Target": round(target_hours),
                        "Required HC": row['Required HC'],
                        "Actual HC": actual_hc,
                        "Gap (Agents)": actual_hc - row['Required HC']
                    })

            st.table(pd.DataFrame(final_results))
    except Exception as e:
        st.error(f"خطأ: {e}")
