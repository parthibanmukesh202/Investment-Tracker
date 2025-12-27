import streamlit as st
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import numpy as np
import os

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Cashflow Investment Dashboard", layout="wide")

DATA_DIR = "user_data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- STYLING ----------------
st.markdown("""
<style>
.main { background-color: #f4f7f6; }
[data-testid="stMetricValue"] { color: #2e7d32; font-size: 1.6rem; font-weight: 700; }
[data-testid="stMetricLabel"] { color: #555; font-size: 1rem; }
.stButton>button {
    background-color: #2e7d32;
    color: white;
    border-radius: 8px;
    border: none;
    height: 3em;
    font-weight: bold;
    width: 100%;
}
.stButton>button:hover { background-color: #1b5e20; }
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
st.sidebar.title("🔐 Login")
username = st.sidebar.text_input("Enter your username").strip()

if not username:
    st.title("🔒 Cashflow Investment Dashboard")
    st.info("Enter your username in the sidebar to continue")
    st.stop()

user_file = os.path.join(DATA_DIR, f"{username}.csv")

# ---------------- LOAD / INIT DATA ----------------
if os.path.exists(user_file):
    df = pd.read_csv(user_file)
    df["Date"] = pd.to_datetime(df["Date"])
else:
    df = pd.DataFrame({
        "Date": [date.today()],
        "Cashflow": [0.0]
    })

# ---------------- XIRR FUNCTION ----------------
def calculate_xirr(cashflows, dates, guess=0.1):
    if len(cashflows) < 2:
        return 0.0
    if all(x >= 0 for x in cashflows) or all(x <= 0 for x in cashflows):
        return 0.0

    years = [(d - dates[0]).days / 365.25 for d in dates]
    rate = guess

    for _ in range(100):
        try:
            f = sum(cf / (1 + rate) ** t for cf, t in zip(cashflows, years))
            df_val = sum(-t * cf / (1 + rate) ** (t + 1) for cf, t in zip(cashflows, years))
            if df_val == 0:
                break
            new_rate = rate - f / df_val
            if abs(new_rate - rate) < 1e-6:
                return new_rate
            rate = new_rate
        except:
            return 0.0
    return 0.0

# ---------------- HEADER ----------------
st.title("💰 Cashflow XIRR Dashboard")
st.markdown(f"Created by **Mukesh Parthiban** | User: **{username}**")
st.divider()

# ---------------- LAYOUT ----------------
left, right = st.columns([1.3, 1])

# ---------------- LEFT : CASHFLOW ----------------
with left:
    st.subheader("🗓️ Cashflow Entry")

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        height=420,
        column_config={
            "Date": st.column_config.DateColumn("Date"),
            "Cashflow": st.column_config.NumberColumn(
                "Cashflow (₹)  (- for Invest, + for Return)",
                format="₹ %.2f"
            )
        }
    )

    if st.button("💾 Save My Data"):
        edited_df.to_csv(user_file, index=False)
        st.success("Data saved successfully!")

# ---------------- RIGHT : CALCULATIONS ----------------
with right:
    st.subheader("📊 Investment Summary")

    calc_df = edited_df.dropna().copy()
    calc_df["Date"] = pd.to_datetime(calc_df["Date"])
    calc_df = calc_df.sort_values("Date")

    if not calc_df.empty:
        invested = abs(calc_df[calc_df["Cashflow"] < 0]["Cashflow"].sum())
        total_cashflow = calc_df["Cashflow"].sum()
        net_value = invested + total_cashflow
        profit = net_value - invested
        abs_return = profit / invested if invested > 0 else 0

        xirr = calculate_xirr(
            calc_df["Cashflow"].tolist(),
            calc_df["Date"].tolist()
        )

        if len(calc_df) > 1 and invested > 0:
            years = (calc_df["Date"].max() - calc_df["Date"].min()).days / 365.25
            cagr = (net_value / invested) ** (1 / years) - 1 if years > 0 else 0
        else:
            cagr = 0.0

        m1, m2 = st.columns(2)
        m1.metric("💸 Total Invested", f"₹ {invested:,.0f}")
        m2.metric("💰 Net Value", f"₹ {net_value:,.0f}")

        m3, m4, m5 = st.columns(3)
        m3.metric("📈 Profit", f"₹ {profit:,.0f}")
        m4.metric("📊 CAGR", f"{cagr:.2%}")
        m5.metric("🎯 XIRR", f"{xirr:.2%}")

        st.markdown(f"**Absolute Return:** {abs_return:.2%}")

        if invested > 0:
            fig, ax = plt.subplots()
            ax.pie(
                [invested, max(0, profit)],
                labels=["Invested", "Profit"],
                autopct="%1.1f%%",
                startangle=140
            )
            centre = plt.Circle((0, 0), 0.7, fc="white")
            fig.gca().add_artist(centre)
            st.pyplot(fig)

# ---------------- SIP / LUMPSUM ----------------
st.divider()
st.subheader("🚀 SIP / Lumpsum Calculator")

mode = st.radio("Mode", ["SIP", "Lumpsum"], horizontal=True)

c1, c2, c3 = st.columns(3)

if mode == "SIP":
    sip = c1.number_input("Monthly SIP (₹)", value=10000)
    ret = c2.number_input("Expected Return (%)", value=12.0)
    yrs = c3.number_input("Years", value=15)

    r = ret / 100 / 12
    n = yrs * 12
    invested_amt = sip * n
    corpus = sip * (((1 + r) ** n - 1) / r) * (1 + r)

else:
    lump = c1.number_input("Lumpsum Amount (₹)", value=100000)
    ret = c2.number_input("Expected Return (%)", value=12.0)
    yrs = c3.number_input("Years", value=15)

    invested_amt = lump
    corpus = lump * (1 + ret / 100) ** yrs

o1, o2, o3 = st.columns(3)
o1.metric("Invested", f"₹ {invested_amt:,.0f}")
o2.metric("Returns", f"₹ {corpus - invested_amt:,.0f}")
o3.metric("Final Value", f"₹ {corpus:,.0f}")

