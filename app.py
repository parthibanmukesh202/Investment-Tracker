import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Investment Tracker", layout="wide")

# --- LOGIN ---
st.sidebar.title("🔐 Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if not (username and password == "invest123"):
    st.info("Login using password: invest123")
    st.stop()

# --- CONNECT SHEET ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    data = conn.read()
except:
    data = pd.DataFrame(columns=["User", "Date", "Cashflow"])

user_df = data[data["User"] == username]

if user_df.empty:
    user_df = pd.DataFrame({
        "User": [username],
        "Date": [date.today()],
        "Cashflow": [0.0]
    })

st.title("💰 Investment Dashboard")
st.write(f"Welcome **{username}**")

# --- EDITOR ---
edited = st.data_editor(
    user_df[["Date", "Cashflow"]],
    num_rows="dynamic",
    use_container_width=True
)

# --- AUTO SAVE ---
other_users = data[data["User"] != username]
edited["User"] = username
final_df = pd.concat([other_users, edited], ignore_index=True)

conn.update(data=final_df)

st.success("✅ Auto-saved to Google Sheets")

