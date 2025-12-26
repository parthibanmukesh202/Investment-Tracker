import streamlit as st
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import gspread
from google.oauth2.service_account import Credentials

# ---------------- CONFIG ----------------
st.set_page_config("Investment Dashboard", layout="wide")

# ---------------- GOOGLE SHEETS CONNECT ----------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open(st.secrets["app"]["sheet_name"]).sheet1

# ---------------- LOGIN ----------------
st.sidebar.title("🔐 Login")
username = st.sidebar.text_input("Enter your name").strip()

if not username:
    st.title("🔒 Investment Dashboard")
    st.info("Please enter your name in sidebar to continue")
    st.stop()

# ---------------- LOAD DATA ----------------
data = sheet.get_all_records()
df = pd.DataFrame(data)

if df.empty:
    df = pd.DataFrame(columns=["User", "Date", "Cashflow"])

user_df = df[df["User"] == username].copy()

# ---------------- TITLE ----------------
st.title("💰 Investment Dashboard")
st.markdown(f"Created by **Mukesh Parthiban** | User: **{username}**")
st.divider()

# ---------------- ADD CASHFLOW ----------------
st.subheader("➕ Add Cashflow")

c1, c2, c3 = st.columns(3)
cf_date = c1.date_input("Date", value=date.today())
cf_amt = c2.number_input("Cashflow (₹)", value=0.0, step=500.0)

if c3.button("SAVE"):
    sheet.append_row([username, str(cf_date), cf_amt])
    st.success("Saved successfully ✅")
    st.rerun()

# ---------------- DISPLAY DATA ----------------
st.subheader("📒 Cashflow History")

user_df["Date"] = pd.to_datetime(user_df["Date"])
user_df = user_df.sort_values("Date")

st.dataframe(user_df[["Date", "Cashflow"]], use_container_width=True)

# ---------------- SUMMARY ----------------
if not user_df.empty:
    invested = abs(user_df[user_df["Cashflow"] < 0]["Cashflow"].sum())
    returns = user_df["Cashflow"].sum() + invested
    gain = returns - invested

    col1, col2, col3 = st.columns(3)
    col1.metric("💸 Invested", f"₹ {invested:,.0f}")
    col2.metric("💰 Current Value", f"₹ {returns:,.0f}")
    col3.metric("📈 Gain", f"₹ {gain:,.0f}")

    fig, ax = plt.subplots()
    ax.pie(
        [invested, max(gain, 0)],
        labels=["Investment", "Profit"],
        autopct="%1.1f%%",
        startangle=90
    )
    st.pyplot(fig)

# ---------------- SIP / LUMPSUM ----------------
st.divider()
st.subheader("🚀 SIP & Lumpsum Calculator")

mode = st.radio("Select Mode", ["SIP", "Lumpsum"], horizontal=True)

a, b, c = st.columns(3)
rate = b.number_input("Expected Return %", value=12.0)
years = c.number_input("Years", value=15)

if mode == "SIP":
    sip = a.number_input("Monthly SIP ₹", value=10000)
    m = years * 12
    r = rate / 12 / 100
    corpus = sip * (((1 + r) ** m - 1) / r) * (1 + r)
    invested = sip * m
else:
    lump = a.number_input("Lumpsum ₹", value=100000)
    corpus = lump * (1 + rate / 100) ** years
    invested = lump

c1, c2, c3 = st.columns(3)
c1.metric("Invested", f"₹ {invested:,.0f}")
c2.metric("Returns", f"₹ {corpus - invested:,.0f}")
c3.metric("Future Value", f"₹ {corpus:,.0f}")
