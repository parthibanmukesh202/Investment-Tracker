import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Cashflow XIRR Dashboard", layout="wide")

st.title("💰 Cashflow XIRR Dashboard")
st.caption("Created by Mukesh Parthiban")
st.divider()

# ---------------- LOGIN ----------------
st.sidebar.title("🔐 Login")
username = st.sidebar.text_input("Enter your username")

if not username:
    st.warning("👈 Please enter username to continue")
    st.stop()

# ---------------- GOOGLE SHEETS CONNECTION ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

# 👉 OPEN YOUR GOOGLE SHEET (NAME MUST MATCH)
sheet = client.open("InvestmentData").worksheet("cashflows")

# ---------------- LOAD USER DATA ----------------
data = sheet.get_all_records()
df = pd.DataFrame(data)

if df.empty:
    df = pd.DataFrame(columns=["username", "date", "cashflow"])

user_df = df[df["username"] == username].copy()

if not user_df.empty:
    user_df["date"] = pd.to_datetime(user_df["date"]).dt.date

# ---------------- ADD CASHFLOW ----------------
st.subheader("➕ Add Cashflow")

col1, col2 = st.columns(2)
with col1:
    c_date = st.date_input("Date", value=date.today())
with col2:
    c_amount = st.number_input(
        "Cashflow (Investment = negative)",
        step=500.0,
        format="%.2f"
    )

if st.button("Save Cashflow"):
    sheet.append_row([username, str(c_date), float(c_amount)])
    st.success("✅ Cashflow saved permanently")
    st.rerun()

# ---------------- SHOW CASHFLOWS ----------------
st.subheader("📒 Your Cashflows")

if user_df.empty:
    st.info("No cashflows yet")
else:
    st.dataframe(user_df[["date", "cashflow"]], use_container_width=True)

# ---------------- XIRR FUNCTION ----------------
def calculate_xirr(cashflows, dates):
    if len(cashflows) < 2:
        return 0.0

    import numpy as np

    days = np.array([(d - dates[0]).days for d in dates]) / 365
    guess = 0.1

    for _ in range(100):
        f = sum(c / (1 + guess) ** t for c, t in zip(cashflows, days))
        df = sum(-t * c / (1 + guess) ** (t + 1) for c, t in zip(cashflows, days))
        if df == 0:
            break
        new_guess = guess - f / df
        if abs(new_guess - guess) < 1e-6:
            return new_guess
        guess = new_guess

    return 0.0

# ---------------- SUMMARY ----------------
st.divider()
st.subheader("📊 Investment Summary")

if not user_df.empty:
    invested = abs(user_df[user_df["cashflow"] < 0]["cashflow"].sum())
    total = user_df["cashflow"].sum() + invested
    profit = total - invested

    if len(user_df) >= 2:
        xirr = calculate_xirr(
            user_df["cashflow"].tolist(),
            user_df["date"].tolist()
        )
    else:
        xirr = 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("💸 Invested", f"₹ {invested:,.0f}")
    c2.metric("💰 Value", f"₹ {total:,.0f}")
    c3.metric("🎯 XIRR", f"{xirr:.2%}")
else:
    st.info("Add cashflows to see summary")

st.caption("🔒 Data auto-saved in Google Sheet | Refresh-safe | User-specific")
