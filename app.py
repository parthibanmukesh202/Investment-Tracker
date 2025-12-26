import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import date
import matplotlib.pyplot as plt

# --- APP CONFIG ---
st.set_page_config(page_title="Investment Tracker", layout="wide")

# Google Sheets Connection
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("💰 Investment Dashboard")
st.markdown('📊 Created by **Mukesh Parthiban**')

# --- USER LOGIN ---
user = st.sidebar.text_input("Enter Your Name:", value="").strip()

if user:
    # Load Data from Sheets
    try:
        df = conn.read(ttl=0)
    except:
        df = pd.DataFrame(columns=["User", "Date", "Cashflow"])

    # Filter for User
    user_df = df[df["User"] == user].copy()
    
    if user_df.empty:
        st.info(f"Welcome {user}! Starting fresh.")
        user_df = pd.DataFrame([{"User": user, "Date": str(date.today()), "Cashflow": 0.0}])

    # --- UI LAYOUT (Unga Pazhaya Format) ---
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.subheader(f"🗓️ {user}'s Cashflow Journal")
        # Editable Table
        edited_df = st.data_editor(user_df[["Date", "Cashflow"]], num_rows="dynamic", use_container_width=True)

        if st.button("💾 Save Changes Permanently"):
            other_users = df[df["User"] != user] if not df.empty else pd.DataFrame()
            edited_df["User"] = user
            final_df = pd.concat([other_users, edited_df], ignore_index=True)
            conn.update(data=final_df)
            st.success("Data saved to Google Sheets!")
            st.rerun()

    with col_right:
        st.subheader("📌 Summary & Analytics")
        if not edited_df.empty:
            # Calculation
            total = pd.to_numeric(edited_df["Cashflow"]).sum()
            st.metric("Net Balance", f"₹ {total:,.2f}")
            
            # Graphs (Unga pazhaya graph format)
            fig, ax = plt.subplots()
            edited_df.plot(kind='line', x='Date', y='Cashflow', ax=ax, marker='o', color='#2e7d32')
            plt.xticks(rotation=45)
            st.pyplot(fig)
else:
    st.warning("👈 Please enter your name in the sidebar to access your dashboard.")
