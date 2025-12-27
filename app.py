import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from scipy.optimize import newton

# ----------------- BASIC CONFIG -----------------
st.set_page_config(page_title="Investment Dashboard", layout="wide")

DATA_FILE = "data.csv"

# ----------------- HELPERS -----------------
def load_data():
    try:
        return pd.read_csv(DATA_FILE)
    except:
        return pd.DataFrame(columns=["username", "date", "amount"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def calculate_xirr(dates, cashflows):
    if len(cashflows) < 2:
        return None

    def xnpv(rate):
        return sum(cf / ((1 + rate) ** ((d - dates[0]).days / 365))
                   for cf, d in zip(cashflows, dates))

    try:
        return newton(xnpv, 0.1)
    except:
        return None

def calculate_cagr(dates, values):
    if len(values) < 2:
        return None
    years = (dates[-1] - dates[0]).days / 365
    if years <= 0:
        return None
    return (values[-1] / abs(values[0])) ** (1 / years) - 1

def safe_percent(x):
    if x is None or np.isnan(x) or abs(x) > 5:
        return "N/A"
    return f"{x*100:.2f}%"

# ----------------- LOGIN -----------------
st.sidebar.title("🔐 Login")
username = st.sidebar.text_input("Enter your username")

if not username:
    st.stop()

# ----------------- LOAD USER DATA -----------------
df = load_data()
user_df = df[df["username"] == username]

# ----------------- INPUT SECTION -----------------
st.title("💰 Investment Tracker")

col1, col2 = st.columns(2)

with col1:
    input_date = st.date_input("Date", value=date.today())

with col2:
    amount = st.number_input("Cashflow (Invest = -, Return = +)", step=100)

if st.button("➕ Add Cashflow"):
    new_row = pd.DataFrame([[username, input_date, amount]],
                           columns=["username", "date", "amount"])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    st.success("Saved successfully")
    st.experimental_rerun()

# ----------------- DATA PREP -----------------
user_df = df[df["username"] == username]
user_df["date"] = pd.to_datetime(user_df["date"])
user_df = user_df.sort_values("date")

# ----------------- METRICS -----------------
if not user_df.empty:
    invested = abs(user_df[user_df["amount"] < 0]["amount"].sum())
    total = user_df["amount"].sum()
    profit = total + invested

    dates = list(user_df["date"])
    cashflows = list(user_df["amount"])
    values = list(user_df["amount"].cumsum())

    xirr = calculate_xirr(dates, cashflows)
    cagr = calculate_cagr(dates, values)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("💸 Invested", f"₹ {invested:,.0f}")
    m2.metric("💰 Net Value", f"₹ {total + invested:,.0f}")
    m3.metric("📈 Profit", f"₹ {profit:,.0f}")
    m4.metric("📊 CAGR", safe_percent(cagr))
    m5.metric("🎯 XIRR", safe_percent(xirr))

# ----------------- CHARTS -----------------
st.divider()

if not user_df.empty:
    user_df["cumulative"] = user_df["amount"].cumsum()

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📈 Investment Growth")
        st.line_chart(user_df.set_index("date")["cumulative"])

    with c2:
        st.subheader("🥧 Investment Split")
        pie_data = pd.DataFrame({
            "Type": ["Invested", "Profit"],
            "Value": [invested, profit]
        })
        st.pyplot(
            pie_data.set_index("Type").plot.pie(
                y="Value", autopct="%1.1f%%", legend=False
            ).figure
        )

# ----------------- TABLE -----------------
st.divider()
st.subheader("📋 Cashflow History")
st.dataframe(user_df[["date", "amount"]], use_container_width=True)

