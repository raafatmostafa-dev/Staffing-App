import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime, time
import os
import base64

# --- 1. Page Config ---
st.set_page_config(page_title="WFM Professional Suite", layout="wide")

# --- Background ---
def set_bg_image(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            img_data = f.read()
        b64_encoded = base64.b64encode(img_data).decode()
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{b64_encoded}");
            background-size: cover;
            background-position: center;
        }}
        </style>
        """, unsafe_allow_html=True)

# --- Save Files ---
def save_file(uploaded_file, name):
    with open(name, "wb") as f:
        f.write(uploaded_file.getbuffer())

# --- Auth ---
def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    set_bg_image("background.jpg")

    st.markdown("<h2 style='text-align:center;color:white;'>🔒 WFM Secure Access</h2>", unsafe_allow_html=True)

    _, col, _ = st.columns([1,1,1])
    with col:
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")

        if st.button("Login"):
            if user == "Raafat Mostafa" and pw == "Rr#01010353831":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid credentials")

    return False


# ================= MAIN =================
if check_auth():

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Capacity Dashboard",
        "🎯 Resource Requirements",
        "🗓️ Scheduling",
        "⚖️ Net Staffing"
    ])

    # ================= TAB 1 =================
    with tab1:
        with st.sidebar:
            st.header("⚙️ Configuration")

            d_range = st.date_input("Analysis Period", [date(2026,2,1), date(2026,2,28)])
            start_date = d_range[0]
            end_date = d_range[1] if len(d_range) > 1 else d_range[0]

            up_main = st.file_uploader("Upload Data.xlsx", type=["xlsx"])
            if up_main:
                save_file(up_main, "data_last.xlsx")

            up_intra = st.file_uploader("Upload Requirements.xlsx", type=["xlsx"])
            if up_intra:
                save_file(up_intra, "intra_last.xlsx")

            up_sched = st.file_uploader("Upload Schedules.xlsx", type=["xlsx"])
            if up_sched:
                save_file(up_sched, "sched_last.xlsx")

        if os.path.exists("data_last.xlsx"):
            try:
                df_all = pd.read_excel("data_last.xlsx")

                working_days = np.busday_count(
                    np.datetime64(start_date),
                    np.datetime64(end_date) + np.timedelta64(1, 'D')
                )

                base_hrs = working_days * 8

                for _, row in df_all.iterrows():
                    lang = row.iloc[0]
                    target = float(row.iloc[1])
                    hc = float(row.iloc[2])
                    shrink = float(row.iloc[3]) / 100

                    available = hc * base_hrs * (1 - shrink)
                    variance = available - target

                    st.metric(f"{lang}", f"{int(available)}h", delta=int(variance))

            except Exception as e:
                st.error(f"Error in data file: {e}")

    # ================= TAB 2 =================
    with tab2:
        if os.path.exists("intra_last.xlsx"):
            try:
                xls = pd.ExcelFile("intra_last.xlsx")
                lang = st.selectbox("Select Language", xls.sheet_names)

                st.session_state['active_lang'] = lang

                df = pd.read_excel("intra_last.xlsx", sheet_name=lang)
                st.dataframe(df, use_container_width=True)

            except Exception as e:
                st.error(f"Error reading intra file: {e}")

    # ================= TAB 3 =================
    with tab3:
        lang = st.session_state.get('active_lang')

        if not lang:
            st.warning("Select language first from tab 2")
        elif os.path.exists("sched_last.xlsx"):
            try:
                df = pd.read_excel("sched_last.xlsx", sheet_name=lang)

                st.dataframe(df, use_container_width=True)

            except Exception as e:
                st.error(f"Error in schedule: {e}")

    # ================= TAB 4 =================
    with tab4:
        if 'df_intra' not in st.session_state:
            st.warning("No data available yet")
        else:
            st.write("Net staffing will appear here")
