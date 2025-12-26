import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import date

# --- APP CONFIG ---
st.set_page_config(page_title="Investment Tracker", layout="wide")

# Google Sheets Connection setup
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("💰 Permanent Investment Dashboard")

# --- USER LOGIN ---
# Indha name-ah vechu dhaan data separate-ah save aagum
user = st.sidebar.text_input("Enter Your Name:", value="").strip()

if user:
    # Google Sheet-la irundhu fresh data-va load pannum
    try:
        df = conn.read(ttl=0) 
    except:
        df = pd.DataFrame(columns=["User", "Date", "Cashflow"])

    # Current user-oda data-va mattum filter pannum
    user_df = df[df["User"] == user].copy()
    
    if user_df.empty:
        st.info(f"Welcome {user}! New account created for you.")
        user_df = pd.DataFrame([{"User": user, "Date": str(date.today()), "Cashflow": 0.0}])

    # Editable Table - User inga dhaan entries poduvaanga
    st.subheader(f"📊 {user}'s Data Journal")
    edited_df = st.data_editor(user_df[["Date", "Cashflow"]], num_rows="dynamic", use_container_width=True)

    if st.button("💾 Save All Changes Permanently"):
        # Pazhaya data-vum pudhu data-vum merge aagum
        other_users = df[df["User"] != user] if not df.empty else pd.DataFrame()
        edited_df["User"] = user
        final_df = pd.concat([other_users, edited_df], ignore_index=True)
        
        # Google Sheet-la update pannum
        conn.update(data=final_df)
        st.success(f"Success! Data saved permanently for {user}.")
        st.rerun()
else:
    st.warning("👈 Please enter your name in the sidebar to load your personal dashboard.")
