import streamlit as st
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import gspread
from google.oauth2.service_account import Credentials

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Cashflow XIRR Dashboard", layout="wide")

# ---------------- GOOGLE SHEET CONNECT ----------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "service_account.json",
    scopes=scope
)

gc = gspread.authorize(creds)
sheet = gc.open("InvestmentDashboard")
users_ws = sheet.worksheet("users")
cashflow_ws = sheet.worksheet("cashflows")

# ---------------- FUNCTIONS ----------------
def calculate_xirr(cashflows, dates, guess=0.1):
    if len(cashflows) < 2:
        return 0.0
    years = [(d - dates[0]).days / 365.25 for d in dates]
    rate = guess
    for _ in range(100):
        f = sum(cf / (1 + rate) ** t for cf, t in zip(cashflows, years))
        df = sum(-t * cf / (1 + rate) ** (t + 1) for cf, t in zip(cashflows, years))
        if df == 0:
            break
        new_rate = rate - f / df
        if abs(new_rate - rate) < 1e-6:
            return new_rate
        rate = new_rate
    return 0.0

# ---------------- LOAD USERS ----------------
users_df = pd.DataFrame(users_ws.get_all_records())

# ---------------- SIDEBAR LOGIN ----------------
st.sidebar.title("🔐 Login")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if username == "" or password == "":
    st.warning("Please login from sidebar")
    st.stop()

user_row = users_df[
    (users_df["username"] == username) &
    (users_df["password"] == password)
]

if user_row.empty:
    st.error("Invalid username or password")
    st.stop()

# ---------------- LOAD CASHFLOWS ----------------
cash_df = pd.DataFrame(cashflow_ws.get_all_records())

user_df = cash_df[cash_df["username"] == username].copy()

if user_df.empty:
    user_df = pd.DataFrame({
        "username": [username],
        "date": [date.today()],
        "cashflow": [-1000]
    })

user_df["date"] = pd.to_datetime(user_df["date"])

# ---------------- UI ----------------
st.title("💰 Cashflow XIRR Dashboard")
st.markdown(f"👤 User: **{username}**")
st.divider()

left, right = st.columns([1.3, 1])

# ---------------- LEFT: CASHFLOW ENTRY ----------------
with left:
    st.subheader("🗓️ Cashflows")

    edited_df = st.data_editor(
        user_df[["date", "cashflow"]],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "date": st.column_config.DateColumn("Date"),
            "cashflow": st.column_config.NumberColumn("Cashflow ₹")
        }
    )

    if st.button("💾 Save"):
        edited_df["username"] = username
        others = cash_df[cash_df["username"] != username]
        final_df = pd.concat([others, edited_df], ignore_index=True)

        cashflow_ws.clear()
        cashflow_ws.update(
            [final_df.columns.tolist()] +
            final_df.astype(str).values.tolist()
        )

        st.success("Saved successfully")
        st.rerun()

# ---------------- RIGHT: SUMMARY ----------------
with right:
    st.subheader("📊 Summary")

    df = edited_df.dropna().copy()
    df = df.sort_values("date")

    invested = abs(df[df["cashflow"] < 0]["cashflow"].sum())
    net = df["cashflow"].sum() + invested
    profit = net - invested
    abs_return = profit / invested if invested > 0 else 0
    xirr = calculate_xirr(df["cashflow"].tolist(), df["date"].tolist())

    c1, c2 = st.columns(2)
    c1.metric("Total Invested", f"₹ {invested:,.0f}")
    c2.metric("Net Value", f"₹ {net:,.0f}")

    c3, c4 = st.columns(2)
    c3.metric("Profit", f"₹ {profit:,.0f}")
    c4.metric("XIRR", f"{xirr:.2%}")

    st.markdown(f"**Absolute Return:** {abs_return:.2%}")

    if invested > 0:
        fig, ax = plt.subplots()
        ax.pie(
            [invested, max(0, profit)],
            labels=["Invested", "Profit"],
            autopct="%1.1f%%",
            startangle=90
        )
        st.pyplot(fig)

st.divider()
st.caption("Created by Mukesh Parthiban")

