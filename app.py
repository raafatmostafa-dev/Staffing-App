import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date

# إعدادات الصفحة
st.set_page_config(page_title="WFM Professional Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- تحسين المظهر باستخدام CSS ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    div[data-testid="stExpander"] {
        background-color: #ffffff;
        border: 1px solid #e6e9ef;
        border-radius: 10px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Professional Workforce Dashboard")
st.markdown("---")

# --- Sidebar للتحكم ---
with st.sidebar:
    st.header("📋 Global Settings")
    start_date = st.date_input("Start Date (F3)", date(2024, 1, 1))
    end_date = st.date_input("End Date (F4)", date(2024, 1, 31))
    
    # حساب أيام العمل
    start_np = np.datetime64(start_date, 'D')
    end_np = np.datetime64(end_date, 'D') + np.timedelta64(1, 'D')
    working_days = np.busday_count(start_np, end_np)
    total_hours_month = working_days * 8
    
    st.metric("Working Days", working_days)
    st.metric("Base Hours/Month", total_hours_month)
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])

# --- محتوى الأبلكيشن ---
if uploaded_file:
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, encoding='cp1256')
        
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        col_lang = next((c for c in df.columns if 'lang' in c or 'لغة' in c), None)
        col_target = next((c for c in df.columns if 'target' in c or 'hour' in c or 'مطلوب' in c), None)
        col_actual = next((c for c in df.columns if 'actual' in c or 'hc' in c or 'فعلي' in c), None)
        col_shr = next((c for c in df.columns if 'shrink' in c or 'شرينك' in c), None)

        if col_lang and col_target:
            # تجميع البيانات
            agg_dict = {col_target: 'sum'}
            if col_actual: agg_dict[col_actual] = 'max'
            if col_shr: agg_dict[col_shr] = 'max'
            
            summary = df.groupby(col_lang).agg(agg_dict).reset_index()
            
            # قسم عرض الملخص العام
            st.subheader("🌐 Global Overview")
            total_target_all = summary[col_target].sum()
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Target Hours", f"{round(total_target_all, 1)} hr")
            
            final_report = []
            
            st.markdown("### 📊 Language Detailed Analysis")
            
            for _, row in summary.iterrows():
                lang_name = str(row[col_lang])
                
                with st.expander(f"Analysis for: {lang_name}"):
                    l_col1, l_col2, l_col3 = st.columns(3)
                    
                    init_hc = float(row[col_actual]) if col_actual else 0.0
                    init_shr = float(row[col_shr]) if col_shr else 20.0
                    
                    actual_hc = l_col1.number_input(f"Actual HC ({lang_name})", value=init_hc, key=f"hc_{lang_name}")
                    shrink_val = l_col2.number_input(f"Shrinkage % ({lang_name})", value=init_shr, key=f"sh_{lang_name}") / 100
                    
                    # الحسابات
                    lang_cap = total_hours_month * (1 - shrink_val)
                    req_hc = np.ceil(row[col_target] / lang_cap) if lang_cap > 0 else 0
                    variance_hc = actual_hc - req_hc
                    
                    l_col3.metric("Required HC", int(req_hc), delta=int(variance_hc), delta_color="normal")
                    
                    # إضافة للتقرير النهائي
                    final_report.append({
                        "Language": lang_name,
                        "Target Hours": round(row[col_target], 1),
                        "Required HC": int(req_hc),
                        "Actual HC": int(actual_hc),
                        "Gap": int(variance_hc)
                    })

            # جدول عرض البيانات النهائي
            st.markdown("---")
            st.subheader("📋 Consolidated Staffing Plan")
            report_df = pd.DataFrame(final_report)
            st.dataframe(report_df.style.background_gradient(subset=['Gap'], cmap='RdYlGn'), use_container_width=True)
            
            # رسم بياني احترافي
            st.markdown("### 📈 Visual Gap Analysis")
            fig, ax = plt.subplots(figsize=(10, 4))
            report_df.plot(x='Language', y=['Required HC', 'Actual HC'], kind='bar', ax=ax, color=['#1f77b4', '#ff7f0e'])
            plt.xticks(rotation=0)
            st.pyplot(fig)

        else:
            st.warning("⚠️ Please ensure the file has 'Language' and 'Hours' columns.")

    except Exception as e:
        st.error(f"Error: {e}")
