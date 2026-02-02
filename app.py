import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Workload vs Capacity Planner", layout="wide")

st.title("📊 Staffing Variance & Shrinkage Calculator")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        data = pd.read_excel(uploaded_file)
        data.columns = [str(c).strip().lower() for c in data.columns]
        
        # 1. إعدادات المدخلات في الجنب
        st.sidebar.header("⚙️ Calculations Settings")
        
        # الهيد كاونت الفعلي الحالي
        actual_headcount = st.sidebar.number_input("Actual Headcount (العدد الحالي)", value=10)
        
        # نسبة الشرينكيدج (مثلاً 20%)
        shrinkage_pct = st.sidebar.slider("Shrinkage % (النسبة المفقودة)", 0, 100, 20) / 100
        
        # أيام العمل وساعات الـ Shift
        working_days = st.sidebar.number_input("Working Days (per month)", value=22)
        shift_hours = 8
        
        # 2. الحسابات الأساسية
        # حساب سعة الموظف الواحد (أسبوعياً)
        individual_weekly_paid_hours = (working_days * shift_hours) / 4
        
        # إجمالي الساعات المدفوعة (قبل الشرينكيدج)
        total_paid_hours = actual_headcount * individual_weekly_paid_hours
        
        # إجمالي الساعات الفعلية المتاحة (بعد خصم الشرينكيدج)
        # المعادلة: الساعات المدفوعة × (1 - نسبة الشرينكيدج)
        actual_available_hours = total_paid_hours * (1 - shrinkage_pct)

        # 3. قراءة الساعات المطلوبة من الملف (Target Hours)
        col_hours = next((c for c in data.columns if 'hour' in c or 'ساع' in c), None)
        
        if col_hours:
            target_hours = data[col_hours].tail(4).mean() # متوسط آخر 4 أسابيع كـ Target
            
            # 4. حساب الفارينس (الفرق)
            # الفرق بين الساعات اللي الشغل محتاجها والساعات اللي الناس هتوفرها فعلياً
            variance_hours = actual_available_hours - target_hours
            
            # عرض النتائج في بطاقات (Metrics)
            st.divider()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Target Hours (Required)", f"{round(target_hours)} hr")
            m2.metric("Total Paid Hours", f"{round(total_paid_hours)} hr")
            m3.metric("Actual Available (After Shrinkage)", f"{round(actual_available_hours)} hr")
            
            # لون الفارينس (أخضر لو زيادة، أحمر لو عجز)
            color = "normal" if variance_hours >= 0 else "inverse"
            m4.metric("Variance (Gap)", f"{round(variance_hours)} hr", delta=round(variance_hours), delta_color=color)

            # 5. تحليل النتيجة
            st.subheader("📝 Variance Analysis")
            if variance_hours < 0:
                needed_hours = abs(variance_hours)
                # كام موظف محتاجينهم عشان نغطي العجز (بعد الشرينكيدج)
                extra_agents_needed = int(np.ceil(needed_hours / (individual_weekly_paid_hours * (1 - shrinkage_pct))))
                st.error(f"⚠️ عندك عجز **{round(needed_hours)}** ساعة. محتاج تعين **{extra_agents_needed}** موظفين إضافيين لتغطية العجز مع حساب الشرينكيدج.")
            else:
                st.success(f"✅ مبروك! عندك فائض **{round(variance_hours)}** ساعة عمل بعد حساب الشرينكيدج.")

            # رسم بياني توضيحي
            st.subheader("📊 Workload vs Actual Capacity")
            fig, ax = plt.subplots(figsize=(10, 4))
            categories = ['Target Hours', 'Actual Available (After Shrinkage)']
            values = [target_hours, actual_available_hours]
            ax.bar(categories, values, color=['#555555', '#00CC96' if variance_hours >= 0 else '#FF4B4B'])
            st.pyplot(fig)

        else:
            st.error("❌ تأكد أن الملف يحتوي على عمود الساعات المطلوبة (hours)")

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
