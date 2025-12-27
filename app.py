import streamlit as st
import pandas as pd
from datetime import date
import numpy as np
import matplotlib.pyplot as plt

# ---------------- APP CONFIG ----------------
st.set_page_config(page_title="Investment Tracker", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
<style>
.main { background-color: #f4f7f6; }
[data-testid="stMetricValue"] { color: #2e7d32; font-size: 1.7rem; font-weight: 700; }
[data-testid="stMetricLabel"] { font-size: 0.95rem; color: #444; }
.stButton>button {
    background-color: #2e7d32;
    color: white;
    font-weight: bold;
    border-radius: 8px;
    height: 3em;
}
.creator { color:#555; font-size:14px; }
</style>
""", unsafe_allow_html=True)

st.title("💰 Personal Investment Dashboard")
st.markdown("<p class='creator'>📊 Created by <b>Mukesh Parthiban</b></p>", unsafe_allow_html=True)
st.divider()

# ---------------- SESSION DATA ----------------
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Date", "Cashflow"])

# ---------------- XIRR FUNCTION ----------------
def calculate_xirr(cashflows, dates):
    if len(cashflows) < 2:
        return 0.0
    try:
        years = [(d - dates[0]).days / 365 for d in dates]
        rate = 0.1
        for _ in range(100):
            f = sum(cf / (1 + rate) ** t for cf, t in zip(cashflows, years))
            df = sum(-t * cf / (1 + rate) ** (t + 1) for cf, t in zip(cashflows, years))
            rate -= f / df
        return rate
    except:
        return 0.0

# ---------------- LAYOUT ----------------
left, right = st.columns([1.3, 1])

# ================= LEFT =================
with left:
    st.subheader("🗓️ Cashflow Entry")

    with st.expander("➕ Add Cashflow", expanded=True):
        d = st.date_input("Select Date")
        amt = st.number_input("Cashflow ( - Invest | + Withdraw )", step=500.0)
        if st.button("Add"):
            st.session_state.df = pd.concat(
                [st.session_state.df, pd.DataFrame({"Date":[d], "Cashflow":[amt]})],
                ignore_index=True
            )
            st.rerun()

    st.subheader("📒 Cashflow Table")
    st.session_state.df = st.data_editor(
        st.session_state.df,
        num_rows="dynamic",
        use_container_width=True
    )

# ================= RIGHT =================
with right:
    st.subheader("📊 Investment Summary")

    df = st.session_state.df.dropna()
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")

        invested = abs(df[df["Cashflow"] < 0]["Cashflow"].sum())
        withdrawn = df[df["Cashflow"] > 0]["Cashflow"].sum()
        net_value = invested + df["Cashflow"].sum()
        profit = net_value - invested

        # CAGR
        years = (df["Date"].max() - df["Date"].min()).days / 365
        cagr = (net_value / invested) ** (1 / years) - 1 if invested > 0 and years > 0 else 0

        # XIRR
        xirr = calculate_xirr(df["Cashflow"].tolist(), df["Date"].tolist())

        m1, m2 = st.columns(2)
        m1.metric("💸 Invested", f"₹ {invested:,.0f}")
        m2.metric("💰 Net Value", f"₹ {net_value:,.0f}")

        m3, m4, m5 = st.columns(3)
        m3.metric("📈 Profit", f"₹ {profit:,.0f}")
        m4.metric("📊 CAGR", f"{cagr:.2%}")
        m5.metric("🎯 XIRR", f"{xirr:.2%}")

        # ---- PIE CHART ----
        st.subheader("🥧 Investment vs Withdrawal")
        fig1, ax1 = plt.subplots()
        ax1.pie(
            [invested, max(1, withdrawn)],
            labels=["Investment", "Withdrawal"],
            autopct="%1.1f%%",
            startangle=90
        )
        ax1.axis("equal")
        st.pyplot(fig1)

        # ---- CASHFLOW LINE ----
        st.subheader("📉 Cashflow Timeline")
        st.line_chart(df.set_index("Date")["Cashflow"])

# ================= SIP / LUMPSUM =================
st.divider()
st.subheader("🚀 SIP / Lumpsum Calculator")

mode = st.radio("Select Mode", ["📅 SIP", "🏦 Lumpsum"], horizontal=True)

c1, c2, c3 = st.columns(3)

if mode == "📅 SIP":
    sip = c1.number_input("Monthly SIP (₹)", value=10000)
    rate = c2.number_input("Expected Return %", value=12.0)
    years = c3.number_input("Years", value=15)

    m_rate = rate / 12 / 100
    months = years * 12
    invested = sip * months

    values = []
    corpus = 0
    for m in range(months):
        corpus = (corpus + sip) * (1 + m_rate)
        values.append(corpus)

else:
    lump = c1.number_input("Lumpsum (₹)", value=100000)
    rate = c2.number_input("Expected Return %", value=12.0)
    years = c3.number_input("Years", value=15)

    invested = lump
    values = [lump * (1 + rate/100) ** y for y in range(1, years + 1)]
    corpus = values[-1]

o1, o2, o3 = st.columns(3)
o1.metric("💸 Invested", f"₹ {invested:,.0f}")
o2.metric("📈 Returns", f"₹ {corpus - invested:,.0f}")
o3.metric("🏦 Final Value", f"₹ {corpus:,.0f}")

st.subheader("📈 Growth Chart")
st.line_chart(values)

