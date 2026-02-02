import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime

st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# دالة لتلوين الخلايا (أحمر للعجز وأخضر للزيادة)
def color_net_staffing(val):
    try:
        color = 'red' if val < 0 else 'green' if val > 0 else 'black'
        return f'color: {color}'
    except:
        return None

# --- نظام التبويبات الأربعة ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Capacity Planning", "⏰ Intraday Requirements", "🗓️ Scheduling", "⚖️ Net Staffing"])

# (أكواد Tab 1 و Tab 2 و Tab 3 تظل كما هي في النسخ السابقة لتوفير المساحة)
# تأكد أن متغيرات df_intra و df_coverage معرفة عالمياً أو مخزنة في st.session_state

# --- TAB 4: NET STAFFING ANALYSIS (التابة الجديدة) ---
with tab4:
    st.subheader("Net Staffing: Coverage vs Requirements")
    st.info("هذه التابة تقارن أوتوماتيكياً بين ما تم رفعه في 'Intraday' و 'Scheduling'")

    # التحقق من وجود البيانات في التابات الأخرى
    if 'df_intra' in locals() or 'intra_up' in st.session_state:
        try:
            # ملاحظة: لضمان عمل المقارنة، يفضل تخزين الجداول في Session State
            # هنا سنفترض أن المستخدم رفع الملفين بالفعل
            
            # 1. توحيد الـ Intervals والتواريخ بين الجدولين
            # نطرح: (جدول السكادول) - (جدول الريكوايرد)
            
            # كود مبسط لعملية الطرح:
            df_net = df_coverage.copy()
            common_cols = [c for c in df_coverage.columns if c in df_intra.columns and c != 'Intervals']
            
            for col in common_cols:
                # تحويل القيم لأرقام لضمان الطرح الصحيح
                req = pd.to_numeric(df_intra[col], errors='coerce').fillna(0)
                sched = pd.to_numeric(df_coverage[col], errors='coerce').fillna(0)
                df_net[col] = sched - req

            st.write("### Net Staffing Table (Manned - Required)")
            st.caption("الأحمر يعني عجز (Under-staffed)، الأخضر يعني زيادة (Over-staffed)")

            # 2. عرض الجدول مع التلوين الديناميكي
            styled_df = df_net.style.applymap(color_net_staffing, subset=common_cols)
            st.dataframe(styled_df, use_container_width=True)

            # 3. تحليل سريع للعجز
            total_gap = df_net[common_cols].sum().sum()
            if total_gap < 0:
                st.error(f"⚠️ Total Gap: {int(total_gap)} Man-hours missing this period.")
            else:
                st.success(f"✅ Total Surplus: {int(total_gap)} Man-hours extra.")

        except Exception as e:
            st.warning("يرجى التأكد من رفع ملفات Required و Schedules أولاً واختيار نفس اللغة.")
    else:
        st.write("الرجاء رفع الملفات في التابات السابقة لتفعيل المقارنة.")
