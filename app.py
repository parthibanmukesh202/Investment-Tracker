import streamlit as st
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Investment Dashboard", layout="wide")

st.title("💰 Investment Dashboard")
st.caption("Created by Mukesh Parthiban")
st.divider()

# ---------------- LOGIN ----------------
st.sidebar.title("🔐 Login")

username = st.sidebar.text_input("Username").strip()

if not username:
    st.info("Please enter username to continue")
    st.stop()

DATA_DIR = "user_data"
os.makedirs(DATA_DIR, exist_ok=True)

user_file = f"{DATA_DIR}/{username}.csv"

# ---------------- LOAD / CREATE DATA ----------------
if os.path.exists(user_file):
    df = pd.read_csv(user_file)
    df["Date"] = pd.to_datetime(df["Date"])
else:
    df = pd.DataFrame({
        "Date": [date(2023, 1, 1)],
        "Cashflow": [-3000.0]
    })

# ---------------- XIRR FUNCTION ----------------
def calculate_xirr(cashflows, dates):
    if len(cashflows) < 2:
        return 0.0
    try:
        years = [(d - dates[0]).days / 365.25 for d in dates]
        rate = 0.1
        for _ in range(100):
            f = sum(cf / (1 + rate)**t for cf, t in zip(cashflows, years))
            df = sum(-t * cf / (1 + rate)**(t + 1) for cf, t in zip(cashflows, years))
            rate -= f / df
        return rate
    except:
        return 0.0

# ---------------- UI ----------------
left, right = st.columns([1.3, 1])

with left:
    st.subheader("🗓️ Cashflows")

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Cashflow": st.column_config.NumberColumn("Amount (₹)", format="₹ %.2f"),
            "Date": st.column_config.DateColumn("Date")
        }
    )

    if st.button("💾 Save"):
        edited_df.to_csv(user_file, index=False)
        st.success("Saved successfully")

with right:
    st.subheader("📊 Summary")

    df_calc = edited_df.copy()
    df_calc["Date"] = pd.to_datetime(df_calc["Date"])
    df_calc = df_calc.sort_values("Date")

    invested = abs(df_calc[df_calc["Cashflow"] < 0]["Cashflow"].sum())
    total = df_calc["Cashflow"].sum() + invested
    profit = total - invested
    xirr = calculate_xirr(df_calc["Cashflow"].tolist(), df_calc["Date"].tolist())

    st.metric("Total Invested", f"₹ {invested:,.0f}")
    st.metric("Current Value", f"₹ {total:,.0f}")
    st.metric("Profit", f"₹ {profit:,.0f}")
    st.metric("XIRR", f"{xirr:.2%}")

    if invested > 0:
        fig, ax = plt.subplots()
        ax.pie([invested, max(profit, 0)], labels=["Investment", "Profit"], autopct="%1.1f%%")
        st.pyplot(fig)

