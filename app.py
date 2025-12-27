import streamlit as st
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import os

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Investment Dashboard", layout="wide")

# ---------------- STYLE (YOUR ORIGINAL LOOK) ----------------
st.markdown("""
<style>
.main { background-color: #f4f7f6; }
[data-testid="stMetricValue"] { color: #2e7d32; font-size: 1.8rem; font-weight: 700; }
[data-testid="stMetricLabel"] { color: #555; font-size: 1rem; }
.stButton>button {
    background-color: #2e7d32;
    color: white;
    border-radius: 8px;
    height: 3em;
    font-weight: bold;
}
.stButton>button:hover { background-color: #1b5e20; }
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
st.sidebar.title("🔐 Login")
username = st.sidebar.text_input("Username").strip()

if not username:
    st.info("Enter username to continue")
    st.stop()

# ---------------- FILE SETUP ----------------
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

# ---------------- TITLE ----------------
st.title("💰 Investment Dashboard")
st.markdown("📊 Created by **Mukesh Parthiban**")
st.divider()

# ---------------- MAIN LAYOUT ----------------
col_left, col_right = st.columns([1.2, 1], gap="large")

# -------- LEFT: CASHFLOW JOURNAL --------
with col_left:
    st.subheader("🗓️ Cashflow Journal")

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        height=450,
        column_config={
            "Cashflow": st.column_config.NumberColumn("Amount (₹)", format="₹ %.2f"),
            "Date": st.column_config.DateColumn("Date")
        }
    )

    if st.button("💾 Save Cashflows"):
        edited_df.to_csv(user_file, index=False)
        st.success("Data saved successfully")

# -------- RIGHT: SUMMARY --------
with col_right:
    st.subheader("📌 Investment Summary")

    df_calc = edited_df.copy()
    df_calc["Date"] = pd.to_datetime(df_calc["Date"])
    df_calc = df_calc.sort_values("Date")

    invested = abs(df_calc[df_calc["Cashflow"] < 0]["Cashflow"].sum())
    net_value = df_calc["Cashflow"].sum() + invested
    profit = net_value - invested
    abs_return = profit / invested if invested > 0 else 0
    xirr = calculate_xirr(df_calc["Cashflow"].tolist(), df_calc["Date"].tolist())

    m1, m2 = st.columns(2)
    m1.metric("💸 Total Invested", f"₹ {invested:,.0f}")
    m2.metric("💰 Net Value", f"₹ {net_value:,.0f}")

    st.divider()

    m3, m4 = st.columns(2)
    m3.metric("📈 Profit", f"₹ {profit:,.0f}")
    m4.metric("🎯 XIRR", f"{xirr:.2%}")

    st.markdown(f"**Absolute Return:** {abs_return:.2%}")

    if invested > 0:
        fig, ax = plt.subplots(figsize=(5,4))
        ax.pie(
            [invested, max(profit,0)],
            labels=["Investment", "Profit"],
            autopct="%1.1f%%",
            startangle=140
        )
        centre = plt.Circle((0,0),0.70,fc="white")
        fig.gca().add_artist(centre)
        st.pyplot(fig)

# ---------------- SIP / LUMPSUM ----------------
st.divider()
st.subheader("🚀 Future Value Projections")

calc_type = st.radio("Calculator Mode", ["🔄 SIP Mode", "🏦 Lumpsum Mode"], horizontal=True)
c1, c2, c3 = st.columns(3)

if "SIP" in calc_type:
    sip = c1.number_input("Monthly SIP (₹)", value=10000)
    ret = c2.number_input("Expected Return (%)", value=12.0)
    yrs = c3.number_input("Years", value=15)

    r = ret / 12 / 100
    months = yrs * 12
    invested_amt = sip * months
    future = sip * (((1+r)**months - 1)/r) * (1+r)
    chart = [sip * (((1+r)**m - 1)/r) * (1+r) for m in range(1, months+1)]
else:
    amt = c1.number_input("Lumpsum (₹)", value=100000)
    ret = c2.number_input("Expected Return (%)", value=12.0)
    yrs = c3.number_input("Years", value=15)

    invested_amt = amt
    future = amt * (1+ret/100)**yrs
    chart = [amt * (1+ret/100)**y for y in range(1, yrs+1)]

o1, o2, o3 = st.columns(3)
o1.metric("Total Invested", f"₹ {invested_amt:,.0f}")
o2.metric("Returns", f"₹ {future-invested_amt:,.0f}")
o3.metric("Future Value", f"₹ {future:,.0f}")

st.line_chart(chart)

