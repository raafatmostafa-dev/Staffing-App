import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Multi-Language Staffing", layout="wide")

st.title("📊 Staffing Calculator per Language")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # قراءة الملف ومعالجة الأخطاء
        if uploaded_file.name.endswith('.xlsx'):
            data = pd.read_excel(uploaded_file)
        else:
            data = pd.read_csv(uploaded_file, encoding='cp1256', on_bad_lines='skip')
        
        data.columns = [str(c).strip().lower() for c in data.columns]
        
        # البحث عن الأعمدة الأساسية
        col_lang = next((c for c in data.columns if 'lang' in c or 'لغة' in c), None)
        col_hours = next((c for c in data.columns if 'hour' in c or 'ساع' in c), None)

        if col_lang and col_hours:
            st.sidebar.header("⚙️ Global Settings")
            working_days = st.sidebar.number_input("Working Days (Month)", value=22)
            shrinkage_pct = st.sidebar.slider("Shrinkage %", 0, 100, 20) / 100
            
            # سعة الموظف الواحد الأسبوعية
            weekly_cap_per_agent = ((working_days * 8) / 4) * (1 - shrinkage_pct)

            # تجميع الساعات المطلوبة لكل لغة
            lang_summary = data.groupby(col_lang)[col_hours].mean().reset_index()
            lang_summary.columns = ['Language', 'Target Hours (Avg)']

            st.subheader("📝 Staffing Requirements per Language")
            
            # حساب الهيد كاونت المطلوب لكل لغة
            lang_summary['Agents Needed'] = lang_summary['Target Hours (Avg)'].apply(lambda x: int(np.ceil(x / weekly_cap_per_agent)))
            
            # عرض الجدول
            st.table(lang_summary)

            # رسم بياني للمقارنة بين اللغات
            
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(lang_summary['Language'], lang_summary['Target Hours (Avg)'], color='skyblue', label='Required Hours')
            ax.set_ylabel("Hours")
            ax.set_title("Workload per Language")
            st.pyplot(fig)

            # قسم تفصيلي لكل لغة (إدخال الأرقام الفعلية)
            st.divider()
            st.subheader("🔍 Language Specific Variance")
            
            for index, row in lang_summary.iterrows():
                with st.expander(f"Analysis for: {row['Language']}"):
                    c1, c2 = st.columns(2)
                    actual_hc = c1.number_input(f"Actual HC for {row['Language']}", value=int(row['Agents Needed']), key=f"hc_{row['Language']}")
                    
                    available_hrs = actual_hc * weekly_cap_per_agent
                    variance = available_hrs - row['Target Hours (Avg)']
                    
                    c2.metric("Variance (Hours)", f"{round(variance, 1)} hr", delta=round(variance, 1))
                    
                    if variance < 0:
                        st.error(f"Understaffed: You need more people for {row['Language']}")
                    else:
                        st.success(f"Optimized: {row['Language']} coverage is good.")
        else:
            st.error("❌ تأكد أن الملف يحتوي على عمود للغة (Language) وعمود للساعات (Hours)")

    except Exception as e:
        st.error(f"Error: {e}")
